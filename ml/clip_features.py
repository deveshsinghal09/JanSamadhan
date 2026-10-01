"""Local CLIP image encoder and fixed civic class descriptions."""
from pathlib import Path
import torch
import numpy as np
from PIL import Image,ImageOps
from transformers import CLIPModel,CLIPProcessor
ROOT=Path(__file__).resolve().parents[1]
PROMPTS={
 'Garbage / litter':['a photo of a large pile of dumped garbage and litter on the roadside','a photo of plastic bags and household rubbish dumped on the ground'],
 'Other / review':['a photo of an unrelated object indoors','a photo of a person or animal','a photo of a building or landscape'],
 'Pothole':['a photo of a pothole, a deep hole in an asphalt road','a photo of a road with missing asphalt and a pothole'],
 'Road scene / review':['a photo of a normal paved street with no damage','a photo of an intact asphalt road'],
 'Road surface issue':['a photo of cracked asphalt pavement','a photo of a damaged road surface with cracks and broken pavement'],
 'Streetlight infrastructure':['a photo of a streetlight pole and lamp','a photo of public street lighting'],
 'Traffic sign / review':['a photo of a traffic sign beside the road','a photo of a road sign'],
 'Waterlogging / flooded road':['a photo of a flooded road covered in standing water','a photo of a street submerged in flood water']}
class CivicEncoder:
 def __init__(self,device=None):
  torch.set_num_threads(2)
  self.device=device or ('cuda' if torch.cuda.is_available() else 'cpu')
  self.model=CLIPModel.from_pretrained(ROOT/'data/clip-pretrained',local_files_only=True).to(self.device).eval()
  self.processor=CLIPProcessor.from_pretrained(ROOT/'data/clip-pretrained',local_files_only=True,use_fast=False)
  self.labels=sorted(PROMPTS)
 def image_features(self,images):
  inputs=self.processor(images=images,return_tensors='pt')['pixel_values'].to(self.device)
  with torch.inference_mode():features=self.model.get_image_features(pixel_values=inputs);features=features/features.norm(dim=-1,keepdim=True)
  return features.cpu().numpy()
 def text_features(self):
  vectors=[]
  for label in self.labels:
   inputs={k:v.to(self.device) for k,v in self.processor(text=PROMPTS[label],return_tensors='pt',padding=True).items()}
   with torch.inference_mode():features=self.model.get_text_features(**inputs);features=features/features.norm(dim=-1,keepdim=True);v=features.mean(0);v=v/v.norm()
   vectors.append(v.cpu().numpy())
  return np.stack(vectors)
