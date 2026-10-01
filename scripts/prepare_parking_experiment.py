"""Scene-separated parking experiment with visually inferred category names.

Names describe bay-marking relationships inspected in sample photographs.
The publisher has not confirmed this mapping; these are not legal findings.
"""
import csv,hashlib,itertools,json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/images/v4-parking-prepared'
VISUAL_LABELS={'1':'Parking within bay markings','2':'Parking crossing bay markings','3':'Parking outside marked bays'}

def main():
 with (ROOT/'data/images/v4-parking-audit/inventory.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
 if len(rows)!=6000 or any(r['review_flags'] for r in rows):raise ValueError('Resolve image audit flags before preparation')
 scenes=defaultdict(list)
 for r in rows:scenes[r['scene']].append(r)
 totals=Counter(r['category_code'] for r in rows);best=None
 # Exhaustive label-balance choice, not prediction- or test-performance selection.
 for test in itertools.combinations(sorted(scenes),2):
  rest=sorted(set(scenes)-set(test))
  for validation in itertools.combinations(rest,2):
   parts={'train':sorted(set(rest)-set(validation)),'validation':list(validation),'test':list(test)}
   counts={s:Counter(r['category_code'] for key in keys for r in scenes[key]) for s,keys in parts.items()}
   if any(c[label]<60 for c in counts.values() for label in totals):continue
   error=sum(abs(counts[s][label]/totals[label]-ratio) for s,ratio in [('train',.6),('validation',.2),('test',.2)] for label in totals)
   if best is None or error<best[0]:best=(error,parts,counts)
 if best is None:raise ValueError('Insufficient scene diversity')
 _,parts,counts=best;mapping={key:s for s,keys in parts.items() for key in keys}
 prepared=[]
 for row in rows:
  path=ROOT/row['path']
  prepared.append({'path':row['path'],'label':VISUAL_LABELS[row['category_code']],
   'source':'ParkScope','source_family':'ParkScope-scene-'+row['scene'],
   'group':'ParkScope-scene-'+row['scene'],'split':mapping[row['scene']],
   'pixel_hash':row['pixel_hash'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 pixel_splits=defaultdict(set)
 for r in prepared:pixel_splits[r['pixel_hash']].add(r['split'])
 if any(len(s)>1 for s in pixel_splits.values()):raise ValueError('Pixel leakage')
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'manifest.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(prepared[0]));writer.writeheader();writer.writerows(prepared)
 audit={'retained_images':len(prepared),'groups':len(scenes),'class_counts':{s:dict(c) for s,c in counts.items()},
 'scene_partitions':parts,'source_counts':{'ParkScope':len(prepared)},
 'sources':[{'name':'ParkScope','url':'https://github.com/Nanasaki-Ai/ParkScope','scope':'6000 views of 2000 vehicles; scene-separated experiment. CC BY 4.0 according to dataset YAML.'}],
 'label_policy':'C1/C2/C3 mapped to within/crossing/outside bay markings following visual inspection of 24 side-view images per code plus earlier sample. This is an inferred local visual description, NOT an author-confirmed category mapping or legal finding. All views of a vehicle and all images from a scene share a split.',
 'visual_label_mapping':VISUAL_LABELS,
 'visual_audit':'data/images/v4-parking-audit/category-1.jpg, category-2.jpg, category-3.jpg; 72 side-view images inspected. Some views obscure boundaries. All 6000 images are source-labelled, not individually re-annotated.',
 'limitations':'Not deployable until semantic mapping and external single-photo evaluation are verified. Ten Chinese road scenes, not Lucknow validation. Source experiment uses three vehicle views; a single view may omit evidence. No other-scene negatives. Pixel duplicates checked; visual annotation accuracy and near duplicates need further audit.'}
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({'scenes':parts,'counts':audit['class_counts']},indent=2))

if __name__=='__main__':main()
