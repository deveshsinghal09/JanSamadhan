"""Prepare lossless resized input cache; no additional training examples are created."""
import argparse,csv,os,concurrent.futures
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
def one(row):
 target=ROOT/'.training-tmp/image-cache'/f"{row['sha256']}.png"
 if target.exists():return
 temp=target.with_name(target.stem+'.prefetch.png')
 with Image.open(ROOT/row['path']) as im:image=ImageOps.exif_transpose(im).convert('RGB')
 image.thumbnail((768,768));target.parent.mkdir(parents=True,exist_ok=True);image.save(temp,compress_level=1)
 try:os.replace(temp,target)
 except PermissionError:
  if not target.exists():raise
  temp.unlink(missing_ok=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,default=ROOT/'data/images/v3-prepared/manifest.csv');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
 rows=list(csv.DictReader(args.manifest.open(encoding='utf8')))
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  for i,_ in enumerate(pool.map(one,rows)):
   if i%1000==0:print('Cached',i,'/',len(rows),flush=True)
