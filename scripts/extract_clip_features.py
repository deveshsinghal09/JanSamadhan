"""Cache frozen image embeddings; these are features, not extra training images."""
import csv,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageOps
from ml.clip_features import CivicEncoder
out=ROOT/'data/image-v6-clip-run';out.mkdir(parents=True,exist_ok=True)
manifest=ROOT/'data/images/manifest.csv'
with manifest.open(encoding='utf8') as f:rows=list(csv.DictReader(f))
encoder=CivicEncoder();print('Encoder device',encoder.device,flush=True)
features=np.zeros((len(rows),512),np.float32);done=0
cache=out/'features.npz'
if cache.exists():
 old=np.load(cache);assert str(old['manifest_hash'])==hashlib.sha256(manifest.read_bytes()).hexdigest();features=old['features'];done=int(old['done'])
for start in range(done,len(rows),16):
 images=[]
 for row in rows[start:start+16]:
  path=ROOT/'.training-tmp/image-cache'/f"{row['sha256']}.png"
  if not path.exists():path=ROOT/row['path']
  with Image.open(path) as im:images.append(ImageOps.exif_transpose(im).convert('RGB'))
 batch=encoder.image_features(images);features[start:start+len(batch)]=batch;done=start+len(batch)
 if done%160==0 or done==len(rows):
  np.savez(cache,features=features,done=done,manifest_hash=hashlib.sha256(manifest.read_bytes()).hexdigest())
  print('Encoded',done,'/',len(rows),flush=True)
np.save(out/'text_features.npy',encoder.text_features())
print('Feature extraction complete',flush=True)
