"""Build condition crops with reviewed intact negatives; no deployed files changed.

One exported variant per source filename avoids counting augmentations as new photos.
Fine-grained ambiguous knocked/faded/dirty classes are excluded from this first
visible-damage experiment, rather than silently converted to intact examples.
"""
import csv,hashlib,json,random,re
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/images/v4-sources/sign-defects'
OUT=ROOT/'data/images/v4-sign-prepared'
LABELS=['cracked','deformation','dirty','faded','graffiti','knocked','occluded','ok','other','peeled','perforation','rust','stickers']
TARGET={'cracked','deformation','graffiti','peeled','perforation','rust'}

def main():
 OUT.mkdir(parents=True,exist_ok=True);cropdir=ROOT/'data/images/v4-sources/sign-condition-crops';cropdir.mkdir(exist_ok=True)
 rows=[];seen=set();rejected=Counter()
 def add(path,label,family,source):
  with Image.open(path) as opened:
   im=ImageOps.exif_transpose(opened).convert('RGB');im.load()
   if min(im.size)<64:rejected['small_crop']+=1;return
   pixel=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
  rows.append(dict(path=path.relative_to(ROOT).as_posix(),label=label,source=source,source_family=family,
    pixel_hash=pixel,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 for path in sorted(BASE.glob('*/images/*.jpg')):
  family=path.stem.split('.rf.')[0]
  if family in seen:continue
  seen.add(family)
  ann=path.parent.parent/'labels'/path.with_suffix('.txt').name
  if not ann.exists():continue
  with Image.open(path) as original:
   im=ImageOps.exif_transpose(original).convert('RGB')
   for i,line in enumerate(ann.read_text().splitlines()):
    if not line.strip():continue
    cls,cx,cy,w,h=map(float,line.split());condition=LABELS[int(cls)]
    if condition not in TARGET:rejected['excluded_condition_'+condition]+=1;continue
    if min(w*im.width,h*im.height)<64:rejected['small_box']+=1;continue
    # A little context, with bounds checked against the full exported photo.
    pad=1.12;box=(max(0,int((cx-w*pad/2)*im.width)),max(0,int((cy-h*pad/2)*im.height)),min(im.width,int((cx+w*pad/2)*im.width)),min(im.height,int((cy+h*pad/2)*im.height)))
    target=cropdir/f'{family}-{i}.png';im.crop(box).save(target)
    add(target,'Visible sign damage','RF:'+family,'Roboflow condition annotations')
 decisions=json.loads((ROOT/'data/images/v4-sign-audit/intact-review/decisions.json').read_text())['decisions']
 for d in decisions:
  if d['decision']!='intact_candidate':continue
  path=ROOT/d['path'];number=int(re.search(r'\d+',path.stem).group())
  add(path,'Intact sign candidate','Portugal-sequence:'+str(number//10),'Reviewed Portuguese sign crops')
 # Merge source families sharing identical decoded pixels, drop conflicting labels.
 parent={r['source_family']:r['source_family'] for r in rows}
 def find(k):
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 pixels={}
 for r in rows:
  if r['pixel_hash'] in pixels:parent[find(r['source_family'])]=find(pixels[r['pixel_hash']])
  else:pixels[r['pixel_hash']]=r['source_family']
 groups=defaultdict(list)
 for r in rows:groups[find(r['source_family'])].append(r)
 clean=[]
 for key,group in groups.items():
  labels=defaultdict(set)
  for r in group:labels[r['pixel_hash']].add(r['label'])
  if any(len(x)>1 for x in labels.values()):rejected['conflicting_group']+=len(group);continue
  unique={r['pixel_hash']:r for r in group};clean.append(list(unique.values()))
 best=None;totals=Counter(r['label'] for g in clean for r in g)
 for seed in range(42,542):
  ids=list(range(len(clean)));random.Random(seed).shuffle(ids);a=int(len(ids)*.7);b=int(len(ids)*.85)
  parts={'train':ids[:a],'validation':ids[a:b],'test':ids[b:]}
  counts={s:Counter(r['label'] for i in ix for r in clean[i]) for s,ix in parts.items()}
  if any(c[label]<15 for c in counts.values() for label in totals):continue
  error=sum(abs(counts[s][label]/totals[label]-frac) for s,frac in [('train',.7),('validation',.15),('test',.15)] for label in totals)
  if best is None or error<best[0]:best=(error,seed,parts,counts)
 if best is None:raise ValueError('Too few independent negative groups')
 _,seed,parts,counts=best;prepared=[]
 for split,ids in parts.items():
  for i in ids:
   prepared.extend(r|{'group':'SIGN-'+str(i),'split':split} for r in clean[i])
 with (OUT/'manifest.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(prepared[0]));writer.writeheader();writer.writerows(prepared)
 audit={'retained_images':len(prepared),'groups':len(clean),'class_counts':{s:dict(c) for s,c in counts.items()},'rejected':dict(rejected),'split_seed':seed,
 'sources':[{'name':'Annotated damaged signs','url':'https://universe.roboflow.com/matyworkspace/damaged-traffic-signs/dataset/1'},{'name':'Visually reviewed Portuguese sign crops','url':'https://www.kaggle.com/datasets/danielvareta/damaged-signs-dataset'}],
 'label_policy':'First exported variant per source family; annotated cracked, deformation, graffiti, peeled, perforation, rust crops >=64px; 123 reviewed intact candidates. Other condition classes excluded, not relabelled. Source families and exact duplicates grouped before label-balanced splitting.',
 'limitations':'Experimental crop classifier, not full-scene sign detection. Strong source/quality bias between positives and negatives. Limited intact negatives; contact-sheet audit is not independent field validation. Near-duplicate and full positive visual audits remain pending. No automatic promotion. Does not yet cover every requested sign problem.'}
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({'images':len(prepared),'counts':audit['class_counts'],'rejected':dict(rejected)},indent=2))

if __name__=='__main__':main()
