"""Incremental decoded-pixel audit; never label a pending download as bad data."""
import csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageOps,ImageStat,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/images/v4-electrical-audit'

def main():
 with (OUT/'split_plan.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
 cache_path=OUT/'pixel_cache.json'
 cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
 audited=[];pending=0
 for i,row in enumerate(rows):
  path=ROOT/row['path']
  if not path.exists():pending+=1;continue
  stat=path.stat();stamp=[stat.st_size,stat.st_mtime_ns]
  prior=cache.get(row['path'])
  if prior and prior['stamp']==stamp:result=prior['result']
  else:
   result={'flags':[]}
   try:
    with Image.open(path) as source:
     im=ImageOps.exif_transpose(source).convert('RGB');im.load()
     hasher=hashlib.sha256(str(im.size).encode())
     # Hash rows in strips to bound temporary allocation during GPU training.
     for y in range(0,im.height,64):hasher.update(im.crop((0,y,im.width,min(y+64,im.height))).tobytes())
     small=im.convert('L').resize((17,16));values=list(small.getdata());bits=0
     for y in range(16):
      for x in range(16):bits=(bits<<1)|int(values[y*17+x+1]>values[y*17+x])
     gray=im.convert('L');gray.thumbnail((128,128))
     mean=ImageStat.Stat(gray).mean[0]
     result.update(pixel_hash=hasher.hexdigest(),dhash=str(bits),width=im.width,height=im.height,
       sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mean_luminance=mean)
     if min(im.size)<64:result['flags'].append('too_small_review')
     if mean<15:result['flags'].append('very_dark_review')
     if ImageStat.Stat(gray).stddev[0]<8:result['flags'].append('low_contrast_review')
   except OSError:result['flags'].append('decode_error')
   cache[row['path']]={'stamp':stamp,'result':result}
  audited.append(row|result)
  if i%500==0:
   cache_path.write_text(json.dumps(cache));print('Pixel audit',i,'/',len(rows),flush=True)
 cache_path.write_text(json.dumps(cache))
 groups=defaultdict(list)
 for r in audited:
  if r.get('pixel_hash'):groups[r['pixel_hash']].append(r)
 conflicts=[g for g in groups.values() if len({r['condition'] for r in g})>1]
 cross=[g for g in groups.values() if len({r['planned_split'] for r in g})>1]
 report={'audited':len(audited),'pending_download':pending,'unique_pixels':len(groups),
  'duplicate_groups':sum(len(g)>1 for g in groups.values()),'conflicting_label_groups':len(conflicts),
  'cross_split_pixel_groups':len(cross),'flags':dict(Counter(f for r in audited for f in r['flags'])),
  'ready_for_training':False,
  'policy':'Incomplete until downloads finish. Exact-pixel matches across dates require merged groups before training. Perceptual grouping and visual review remain pending. Flags are review requests, not automatic exclusions.'}
 (OUT/'pixel_audit.json').write_text(json.dumps(report,indent=2))
 (OUT/'pixel_conflicts.json').write_text(json.dumps({'label_conflicts':conflicts,'cross_split_duplicates':cross},indent=2))
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
