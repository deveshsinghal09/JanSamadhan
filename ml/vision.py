"""Shared image model and safe decoding. No network calls during inference."""
import io
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from torchvision import models, transforms

ROOT=Path(__file__).resolve().parents[1]
MODEL_PATH=ROOT/'ml/image_model.pt'
Image.MAX_IMAGE_PIXELS=20_000_000
MEAN=[.485,.456,.406];STD=[.229,.224,.225]
def transform(training=False,size=224,preserve_frame=False):
 if training:
  if preserve_frame:return transforms.Compose([transforms.Resize((size,size)),transforms.RandomHorizontalFlip(),transforms.ColorJitter(.15,.15,.1,.02),transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
  resize=round(size*256/224)
  return transforms.Compose([transforms.Resize((resize,resize)),transforms.RandomResizedCrop(size,scale=(.8,1.)),transforms.RandomHorizontalFlip(),transforms.ColorJitter(.15,.15,.1,.02),transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
 return transforms.Compose([transforms.Resize((size,size)),transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
def architecture(n,pretrained=False,name='mobilenet_v3_small'):
 if name=='mobilenet_v3_large':model=models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretrained else None)
 elif name=='mobilenet_v3_small':model=models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None)
 else:raise ValueError('Unsupported image architecture')
 model.classifier[-1]=torch.nn.Linear(model.classifier[-1].in_features,n)
 return model
def decode_image(raw):
 if len(raw)>3*1024*1024:raise ValueError('Image exceeds 3 MB')
 try:
  with Image.open(io.BytesIO(raw)) as source:
   if source.format not in ('JPEG','PNG'):raise ValueError('Use a PNG or JPEG image')
   if source.width*source.height>20_000_000:raise ValueError('Image exceeds the 20 megapixel decoding limit')
   if source.width<32 or source.height<32:raise ValueError('Image must be at least 32 × 32 pixels')
   source.load();return ImageOps.exif_transpose(source).convert('RGB')
 except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as e:
  raise ValueError('Image is damaged, unsupported or too large to decode') from e
class ImageClassifier:
 def __init__(self,model_path=None,road_model_path=None):
  torch.set_num_threads(2)
  checkpoint=torch.load(model_path or MODEL_PATH,map_location='cpu',weights_only=True)
  self.labels=checkpoint['labels'];self.model=architecture(len(self.labels),name=checkpoint.get('architecture','mobilenet_v3_small'))
  self.model.load_state_dict(checkpoint['state_dict']);self.model.eval()
  self.preprocess=transform(size=checkpoint.get('image_size',224));self.version=checkpoint['version']
  self.max_edge=checkpoint.get('max_edge',768 if self.version.startswith('image-v3') else None)
  self.architecture_name='MobileNetV3-Large' if checkpoint.get('architecture')=='mobilenet_v3_large' else 'MobileNetV3-Small'
  self.threshold=checkpoint.get('review_threshold',.70)
  self.temperature=checkpoint.get('temperature',1.)
  self.class_thresholds=checkpoint.get('class_thresholds',{})
  self.margin=checkpoint.get('review_margin',.15)
  self.road_refiner=ImageClassifier(road_model_path) if road_model_path else None
  self.road_acceptance_validated=False
  if self.road_refiner:
   if set(self.road_refiner.labels)!={'Pothole','Road scene / review','Road surface issue'}:raise ValueError('Road refinement checkpoint has unexpected labels')
   if not set(self.road_refiner.labels).issubset(self.labels):raise ValueError('Base model lacks road labels')
   self.version=f'{self.version}+{self.road_refiner.version}'
   self.architecture_name=f'{self.architecture_name} with {self.road_refiner.architecture_name} road refinement'
 def scores_for_image(self,image):
  if self.max_edge:
   image=image.copy();image.thumbnail((self.max_edge,self.max_edge))
  with torch.inference_mode():scores=torch.softmax(self.model(self.preprocess(image).unsqueeze(0))/self.temperature,dim=1)[0].numpy().copy()
  if self.road_refiner:
   indices=[self.labels.index(label) for label in self.road_refiner.labels]
   scores[indices]=float(scores[indices].sum())*self.road_refiner.scores_for_image(image)
  return scores
 def predict(self,raw):
  image=decode_image(raw)
  scores=self.scores_for_image(image).tolist()
  index=int(np.argmax(scores));label=self.labels[index];score=float(scores[index])
  mapping={'Garbage / litter':'Garbage','Waste material':'Garbage','Pothole':'Road Damage','Road surface issue':'Road Damage'}
  reasons=[]
  if self.road_refiner and label in self.road_refiner.labels and not self.road_acceptance_validated:reasons.append('Experimental road refinement requires validation-calibrated acceptance before automatic routing.')
  if label not in mapping or label=='Road surface issue':reasons.append('This visual class needs an officer to identify the actual complaint.')
  if score<self.class_thresholds.get(label,self.threshold):reasons.append('The prediction does not meet the model’s validation-based acceptance threshold.')
  if sorted(scores)[-1]-sorted(scores)[-2]<self.margin:reasons.append('The photograph has competing visual matches.')
  manual=bool(reasons)
  return {'label':label,'confidence':round(score,4),'scores':dict(zip(self.labels,[round(float(x),4) for x in scores])),
   'suggestedCategory':mapping.get(label) if not manual else None,'manualReview':manual,
   'reviewReasons':reasons,'displayLabel':'Photo needs review' if manual else label,
   'modelVersion':self.version,'method':f'ImageNet-pretrained {self.architecture_name} with supervised civic-image transfer learning; checkpoint selected by validation macro F1',
   'note':'Describe the issue you can see; an officer can review a photo that does not match. Unsupported scenes may still receive a confident label. A model score is not the probability that the complaint is correct.'}
