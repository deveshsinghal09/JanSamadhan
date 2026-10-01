"""Cache road specialist probabilities for validation and test only."""
import csv,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,torch
from PIL import Image,ImageOps
from ml.vision import ImageClassifier
with (ROOT/'data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
model=ImageClassifier(ROOT/'ml/image_road_model.pt');device='cuda' if torch.cuda.is_available() else 'cpu';model.model.to(device)
selected=[i for i,r in enumerate(rows) if r['split']!='train'];q=np.zeros((len(rows),3),np.float32)
for start in range(0,len(selected),8):
 indices=selected[start:start+8];images=[]
 for i in indices:
  r=rows[i];path=ROOT/'.training-tmp/image-cache'/f"{r['sha256']}.png"
  if not path.exists():path=ROOT/r['path']
  with Image.open(path) as im:im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((768,768));images.append(model.preprocess(im))
 with torch.inference_mode():q[indices]=torch.softmax(model.model(torch.stack(images).to(device))/model.temperature,1).cpu().numpy()
 if start%160==0:print('Road evidence',start,'/',len(selected),flush=True)
np.save(ROOT/'data/image-v6-clip-run/road_probabilities.npy',q)
print('Road evidence complete',flush=True)
