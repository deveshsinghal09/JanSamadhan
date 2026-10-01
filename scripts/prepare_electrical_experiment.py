"""Deduplicate electrical crops and split acquisition groups before training."""
import csv,json,random
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'data/images/v4-electrical-audit'
OUT=ROOT/'data/images/v4-electrical-prepared'
LABELS={'good':'Electrical component intact','rust':'Electrical component corrosion','missing_cap':'Insulator missing cap','bird_nest':'Nest on electrical equipment'}

class HashIndex:
 def __init__(self):self.root=None
 def insert(self,value,index):
  node=[value,[index],{}]
  if self.root is None:self.root=node;return
  cursor=self.root
  while True:
   distance=(value^cursor[0]).bit_count()
   if distance==0:cursor[1].append(index);return
   if distance not in cursor[2]:cursor[2][distance]=node;return
   cursor=cursor[2][distance]
 def matches(self,value,radius=4):
  stack=[self.root] if self.root else []
  while stack:
   node=stack.pop();distance=(value^node[0]).bit_count()
   if distance<=radius:yield from node[1]
   stack.extend(child for d,child in node[2].items() if distance-radius<=d<=distance+radius)

def main():
 with (AUDIT/'source_inventory.csv').open(encoding='utf8') as f:original=list(csv.DictReader(f))
 cache=json.loads((AUDIT/'pixel_cache.json').read_text());rows=[];rejected=Counter()
 for row in original:
  path=ROOT/row['path']
  if not path.exists() or row['path'] not in cache:raise ValueError('Download and pixel audit must finish first')
  item=cache[row['path']];stat=path.stat()
  if item['stamp']!=[stat.st_size,stat.st_mtime_ns]:raise ValueError('Stale pixel audit; rerun it')
  if item['result']['flags']:rejected['quality_flag_requires_review']+=1;continue
  rows.append(row|item['result'])
 parent=list(range(len(rows)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 dates={};pixels={};index=HashIndex();near_count=0
 for i,row in enumerate(rows):
  for lookup,key in [(dates,row['capture_date']),(pixels,row['pixel_hash'])]:
   if key in lookup:parent[find(i)]=find(lookup[key])
   else:lookup[key]=i
  value=int(row['dhash'])
  for j in index.matches(value):
   if rows[j]['capture_date']!=row['capture_date']:near_count+=1
   parent[find(i)]=find(j)
  index.insert(value,i)
 groups=defaultdict(list)
 for i,row in enumerate(rows):groups[find(i)].append(row)
 clean=[]
 for group in groups.values():
  bypixel=defaultdict(list)
  for row in group:bypixel[row['pixel_hash']].append(row)
  kept=[]
  for same in bypixel.values():
   if len({r['condition'] for r in same})>1:rejected['conflicting_pixels']+=len(same);continue
   kept.append(same[0]);rejected['exact_duplicates']+=len(same)-1
  if kept:clean.append(kept)
 totals=Counter(r['condition'] for g in clean for r in g);best=None
 for seed in range(42,2042):
  ids=list(range(len(clean)));random.Random(seed).shuffle(ids);a=round(len(ids)*.7);b=round(len(ids)*.85)
  parts={'train':ids[:a],'validation':ids[a:b],'test':ids[b:]}
  counts={s:Counter(r['condition'] for i in ids for r in clean[i]) for s,ids in parts.items()}
  if any(c[label]<20 for c in counts.values() for label in totals):continue
  deviation=sum(abs(counts[s][label]/totals[label]-ratio) for s,ratio in [('train',.7),('validation',.15),('test',.15)] for label in totals)
  if best is None or deviation<best[0]:best=(deviation,seed,parts,counts)
 if best is None:raise ValueError('Insufficient independent acquisition groups after similarity merges')
 _,seed,parts,counts=best;prepared=[]
 for split,ids in parts.items():
  for i in ids:
   for row in clean[i]:
    prepared.append({'path':row['path'],'label':LABELS[row['condition']],'source':'InsPLAD supervised faults','source_family':row['capture_id'],'group':'ELECTRIC-'+str(i),'split':split,'sha256':row['sha256'],'pixel_hash':row['pixel_hash'],'asset':row['asset']})
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'manifest.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(prepared[0]));writer.writeheader();writer.writerows(prepared)
 audit={'retained_images':len(prepared),'groups':len(clean),'class_counts':{s:{LABELS[k]:v for k,v in c.items()} for s,c in counts.items()},'rejected':dict(rejected),'cross_date_near_matches':near_count,'split_seed':seed,
 'sources':[{'name':'InsPLAD supervised fault subset','url':'https://github.com/andreluizbvs/InsPLAD','scope':'CC BY-NC 3.0; public Voxel51 mirror. Crops/augmented examples, not all independent photographs.'}],
 'label_policy':'Original good/rust/missing_cap/bird_nest annotations. Entire acquisition dates, exact pixels and 256-bit dHash radius 4 neighbors grouped before split. Drop conflicting pixels and pending quality flags. Choose split by label counts only.',
 'limitations':'Electrical component crops, not generic full-scene diagnosis or outage detection. Augmented crops may remain in source groups. Some subtle defects need closer visual review. Hardware types and source biases may confound labels. Needs external negative and full-scene checks before deployment; does not cover all electrical problems.'}
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
