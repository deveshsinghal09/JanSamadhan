"""Local civic classifier using a frozen CLIP encoder and supervised civic head."""
import joblib
import numpy as np
from scipy.special import log_softmax,softmax
from ml.clip_features import CivicEncoder,ROOT
from ml.vision import decode_image
class ClipClassifier:
 def __init__(self,artifact_path=None):
  self.artifact=joblib.load(artifact_path or ROOT/'ml/clip_classifier.joblib')
  self.encoder=CivicEncoder(device='cpu');self.labels=self.artifact['labels'];self.version=self.artifact['version']
 def scores_for_image(self,image):
  image=image.copy();image.thumbnail((768,768))
  features=self.encoder.image_features([image])
  linear=self.artifact['model'].decision_function(features)
  semantic=100*features@self.artifact['text_features'].T
  alpha=self.artifact['semantic_weight']
  logits=(1-alpha)*log_softmax(linear,axis=1)+alpha*log_softmax(semantic,axis=1)
  return softmax(logits/self.artifact['temperature'],axis=1)[0]
 def predict(self,raw):
  scores=self.scores_for_image(decode_image(raw));i=int(scores.argmax());label=self.labels[i];confidence=float(scores[i]);reasons=[]
  mapping={'Garbage / litter':'Garbage','Pothole':'Road Damage'}
  if label not in mapping:reasons.append('This visual class needs an officer to identify the actual complaint.')
  if confidence<self.artifact['class_thresholds'][label]:reasons.append('The prediction does not meet the validation-based acceptance threshold.')
  if np.sort(scores)[-1]-np.sort(scores)[-2]<.15:reasons.append('The photograph has competing visual matches.')
  manual=bool(reasons)
  return {'label':label,'confidence':round(confidence,4),'scores':dict(zip(self.labels,[round(float(x),4) for x in scores])),'suggestedCategory':mapping.get(label) if not manual else None,'manualReview':manual,'reviewReasons':reasons,'displayLabel':'Photo needs review' if manual else label,'modelVersion':self.version,'method':'Frozen CLIP ViT-B/32 image encoder with a civic-trained Logistic Regression head and validation-selected semantic blending; temperature fitted on validation data','note':'Photo evidence is combined with your description. Unsupported scenes may still receive a confident label. Model scores do not establish incident truth, jurisdiction or urgency.'}
