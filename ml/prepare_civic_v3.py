"""Build an annotation-led civic scene dataset, excluding the old folder-labeled source.

python -m ml.prepare_civic_v3
No original photograph or existing deployed model is modified.
"""
import csv,json,hashlib,re,random
from pathlib import Path
from collections import Counter,defaultdict
import xml.etree.ElementTree as ET
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageOps
from sklearn.model_selection import train_test_split
from ml.train_images import HashTree,dhash
from ml.vision import ROOT
BASE=ROOT/'data/images/v3-sources';OUT=ROOT/'data/images/v3-prepared'
SEED=42
SOURCES=[
 {'name':'SpotGarbage GINI, explicitly annotated photographs','url':'https://github.com/spotgarbage/spotgarbage-GINI','scope':'Annotated garbage piles/litter; non-garbage photographs used only as review examples. Local academic use; original image rights remain with creators.'},
 {'name':'RDD2022 India','url':'https://doi.org/10.6084/m9.figshare.21431547.v1','scope':'Indian road photographs with PASCAL VOC damage boxes. CC BY-SA 4.0; use labeled training partition only.'},
 {'name':'Roadway Flooding','url':'https://doi.org/10.17632/t395bwcvbw.1','scope':'441 roadway photographs, segmentation masks excluded. CC BY 4.0.'},
 {'name':'Urban Streetlight Analysis','url':'https://github.com/Team16Project/Street-Light-Dataset','scope':'Original streetlight photographs. Combined infrastructure class: daytime/off lamps are NOT evidence of electrical failure. Local academic use; no redistribution.'},
 {'name':'TACO','url':'https://github.com/pedropro/TACO','scope':'Only photos with at least five annotated litter objects and sufficient annotated area; not isolated-object photographs. Local use; per-photo rights retained.'},
 {'name':'Piles of Garbage','url':'https://www.kaggle.com/datasets/hammadarshad18/garbage-detection','scope':'YOLO-annotated garbage piles, Pakistan and web photographs. CC0 listing; overlaps with GINI are deduplicated.'},
 {'name':'Portuguese traffic-sign photographs','url':'https://www.kaggle.com/datasets/danielvareta/damaged-signs-dataset','scope':'500-photo sample. Source labels specify sign type, not condition: used only as Traffic sign / review, never as confirmed damage. CC0 listing.'},
]
# Contact-sheet indices tied to audit/gini-1-index.json, reviewed before splitting.
# Exclude city panoramas, posters/collages, artwork, object-only/bin-only images,
# unclear scenes, natural leaves and isolated wrappers rather than invent labels.
EXCLUDE_GINI={0,1,2,4,21,23,26,30,33,37,44,55,70,84,85,86,90,94,96,99,106,108,109,116,120,125,127,128,130,152,154,155,160,163,164,166,167,168,170,171,174,178,179,181,182,185,193,203,219,226,228,233,236,241,279,281}
def candidates():
 rows=[]
 def add(p,label,source,family=None):
  if p.exists():rows.append({'path':p.relative_to(ROOT).as_posix(),'label':label,'source':source,'source_family':family or source+':'+p.stem})
 index=json.loads((BASE/'audit/gini-1-index.json').read_text())
 excluded={r['image'] for i,r in enumerate(index) if i in EXCLUDE_GINI}
 paths={p.name:p for p in (BASE/'gini').rglob('*') if p.suffix.lower() in ('.jpg','.png','.jpeg') and 'garbage-queried-images' in p.parts}
 for r in csv.DictReader((BASE/'gini-labels.csv').open()):
  if r['label'] not in ('0','1') or r['image'] not in paths or r['image'] in excluded:continue
  add(paths[r['image']],'Garbage / litter' if r['label']=='1' else 'Other / review','GINI')
 for p in sorted((BASE/'garbage-piles').rglob('*')):
  if p.suffix.lower() not in ('.jpg','.jpeg','.png') or p.name in excluded:continue
  annotation=p.with_suffix('.txt')
  if not annotation.exists():continue
  boxes=[line.split() for line in annotation.read_text().splitlines() if line.strip()]
  if not boxes or not all(len(b)==5 for b in boxes):continue
  if all(b[0]=='0' for b in boxes):label='Garbage / litter'
  elif all(b[0]=='2' for b in boxes) and p.stem.startswith('plastic'):label='Other / review'
  else:continue
  date=re.search(r'(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)',p.stem)
  family='Piles:'+''.join(date.groups()) if date else 'GINI:'+p.stem
  add(p,label,'PilesOfGarbage',family)
 (OUT/'visual_exclusions.json').write_text(json.dumps({'source':'GINI','index_file':'data/images/v3-sources/audit/gini-1-index.json','excluded_files':sorted(excluded),'policy':'Visual contact-sheet audit before split; exclude non-scene and ambiguous positives.'},indent=2))
 # All photo/mask pairs are counted separately in the source archive: only photos train.
 for p in sorted((BASE/'roadway-flood').rglob('image_*.jpg')):add(p,'Waterlogging / flooded road','RoadwayFlood')
 for p in sorted((BASE/'sign-scenes').glob('*.jpg')):
  label_file=p.with_suffix('.txt')
  if not label_file.exists():continue
  boxes=[list(map(float,line.split())) for line in label_file.read_text().splitlines() if line.strip()]
  if not boxes:continue
  _,cx,cy,w,h=max(boxes,key=lambda b:b[3]*b[4])
  crop=BASE/'sign-crops'/p.name
  if not crop.exists():
   crop.parent.mkdir(exist_ok=True)
   with Image.open(p) as im:
    width,height=im.size
    if min(w*width,h*height)<32:continue
    # Context around the largest annotated sign; retain one crop per source photo.
    im.convert('RGB').crop((max(0,int((cx-w*.8)*width)),max(0,int((cy-h*.8)*height)),min(width,int((cx+w*.8)*width)),min(height,int((cy+h*.8)*height)))).save(crop,quality=95)
  add(crop,'Traffic sign / review','SignScenes','Signs-sequence-'+str(int(p.stem.split('_')[-1])//10))
 for p in sorted((BASE/'streetlights/Raw Dataset').rglob('*')):
  if p.suffix.lower() in ('.jpg','.jpeg','.png'):
   # Group acquisition days (and WhatsApp transmission dates) conservatively.
   date=re.search(r'(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)',p.stem)
   family='Streetlight:'+''.join(date.groups()) if date else 'Streetlight:'+re.sub(r'\(\d+\)$','',p.stem)
   add(p,'Streetlight infrastructure','Streetlight',family)
 taco=json.loads((ROOT/'data/images/taco_annotations.json').read_text());anns=defaultdict(list)
 for a in taco['annotations']:anns[a['image_id']].append(a)
 for im in taco['images']:
  a=anns[im['id']];area=sum(x.get('area',0) for x in a)/(im['width']*im['height'])
  if len(a)>=5 and area>=.04:
   add(ROOT/f"data/images/raw/taco/taco_{im['id']:05}.jpg",'Garbage / litter','TACO','TACO:'+im['file_name'].split('/')[0])
 # Indian annotated images only; released competition test images have no labels.
 rdd=BASE/'rdd-india';photos={p.stem:p for p in rdd.rglob('*.jpg')}
 for p in sorted(rdd.rglob('*.xml')):
  if p.stem not in photos:continue
  root=ET.parse(p).getroot();names=[x.findtext('name') for x in root.findall('object')]
  if 'D40' in names:label='Pothole'
  elif any(n in ('D00','D10','D20') for n in names):label='Road surface issue'
  else:label='Road scene / review'
  suffix=re.search(r'(\d+)$',p.stem)
  family='RDD-India-sequence-'+str(int(suffix.group())//50) if suffix else 'RDD:'+p.stem
  add(photos[p.stem],label,'RDD2022-India',family)
 if not any(r['source']=='RDD2022-India' for r in rows):raise ValueError('Extract the official Indian road archive and annotations before preparing')
 return rows
def main():
 OUT.mkdir(parents=True,exist_ok=True);raw=candidates();records=[];rejected=Counter();seen=set()
 cache_path=OUT/'hash-cache.json';cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
 def inspect(row):
  p=ROOT/row['path']
  try:
   stat=p.stat();key=row['path'];stamp=[stat.st_size,stat.st_mtime_ns]
   if key in cache and cache[key]['stamp']==stamp:return row|cache[key]['hashes']
   with Image.open(p) as im:
    im=ImageOps.exif_transpose(im).convert('RGB');im.load()
    if min(im.size)<64:return {'error':'too_small'}
    pixel=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
    small=np.asarray(im.convert('L').resize((17,16)),dtype=np.int16)
    h=int.from_bytes(np.packbits(small[:,1:]>small[:,:-1]).tobytes(),'big')
   hashes={'pixel_hash':pixel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'dhash':str(h)}
   cache[key]={'stamp':stamp,'hashes':hashes};return row|hashes
  except (OSError,ValueError):return {'error':'decode_error'}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for index,row in enumerate(pool.map(inspect,raw)):
   if index%1000==0:print('Auditing photos',index,'/',len(raw),flush=True)
   if 'error' in row:rejected[row['error']]+=1;continue
   key=(row['pixel_hash'],row['label'])
   if key in seen:rejected['exact_duplicate']+=1;continue
   seen.add(key);records.append(row)
 cache_path.write_text(json.dumps(cache))
 print('Grouping',len(records),'decoded images',flush=True)
 parent=list(range(len(records)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 families={};pixels={};tree=HashTree()
 for i,r in enumerate(records):
  for lookup,key in [(families,r['source_family']),(pixels,r['pixel_hash'])]:
   if key in lookup:parent[find(i)]=find(lookup[key])
   else:lookup[key]=i
  for j in tree.neighbors(int(r['dhash'])):parent[find(i)]=find(j)
  tree.insert(int(r['dhash']),i)
 groups=defaultdict(list)
 for i,r in enumerate(records):groups[find(i)].append(r)
 # Mixed road-sequence groups are legitimate; retain labels but split the whole group.
 # Exact same pixels with conflicting labels are ambiguous: drop their entire group.
 valid=[]
 for g in groups.values():
  labels=defaultdict(set)
  for r in g:labels[r['pixel_hash']].add(r['label'])
  if any(len(x)>1 for x in labels.values()):rejected['conflicting_pixel_group']+=len(g)
  else:valid.append(g)
 print('Groups',len(valid),'largest',sorted([len(g) for g in valid],reverse=True)[:8],flush=True)
 print('Labels',dict(Counter(r['label'] for g in valid for r in g)),flush=True)
 # Choose a deterministic grouped split with all labels represented in each partition.
 # Split choice uses label counts only, never image predictions or test performance.
 all_labels={r['label'] for r in records};best=None
 for trial in range(200):
  ids=list(range(len(valid)));random.Random(SEED+trial).shuffle(ids)
  a=int(len(ids)*.70);b=int(len(ids)*.85);parts={'train':ids[:a],'validation':ids[a:b],'test':ids[b:]}
  counts={s:Counter(r['label'] for i in ids for r in valid[i]) for s,ids in parts.items()}
  if any(any(c[l]<10 for l in all_labels) for c in counts.values()):continue
  totals=Counter(r['label'] for g in valid for r in g)
  deviation=sum(abs(counts[s][l]/totals[l]-fraction) for s,fraction in [('train',.7),('validation',.15),('test',.15)] for l in all_labels)
  if best is None or deviation<best[0]:best=(deviation,trial,parts,counts)
 if best is None:raise ValueError('Insufficient independent groups for reliable class splits')
 _,trial,parts,counts=best;rows=[]
 for split,ids in parts.items():
  for i in ids:
   for r in valid[i]:rows.append(r|{'group':f'V3-GROUP-{i:05}','split':split})
 with (OUT/'manifest.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 audit={'downloaded_image_files':len(raw),'retained_images':len(rows),'groups':len(valid),'rejected':dict(rejected),'class_counts':{s:dict(c) for s,c in counts.items()},'source_counts':dict(Counter(r['source'] for r in rows)),'split_seed':SEED+trial,'sources':SOURCES,
 'split_policy':'Exact pixels, 256-bit perceptual dHash radius 4, source families, TACO acquisition batches, streetlight dates and consecutive RDD ID blocks of 50 stay in a single split. Approximate 70/15/15 group split, selected for label balance only before training. RDD ID blocks are a conservative sequence heuristic, not verified location separation.',
 'label_policy':'No old Road Issues folder-labeled images; no TrashNet isolated objects. GINI positives are explicitly annotated and visually screened for piles/scattered litter; TACO requires >=5 annotated objects and >=4% annotated area. Flood masks are excluded. Indian road labels come from XML damage annotations. Streetlights are an infrastructure scene class, not a diagnosis of failure.',
 'limitations':'Scene classification, not object detection. Multiple issues may coexist. Streetlight operation, electrical faults, parking legality and sewer blockage cannot be inferred reliably from these labels. No verified Lucknow photo holdout. Source and acquisition biases remain despite group splitting. Dataset sizes count retained original photographs, not augmentation copies. No raw-image redistribution.'}
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
if __name__=='__main__':main()
