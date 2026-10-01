"""Freeze acquisition-date partitions using labels only, before model fitting.

This is a split plan, not a training-ready or visually verified manifest.
"""
import csv,json,random
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/images/v4-electrical-audit'

def main():
 with (OUT/'source_inventory.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
 if any(not r['capture_date'] for r in rows):raise ValueError('Unparsed acquisition date')
 dates=defaultdict(list)
 for row in rows:dates[row['capture_date']].append(row)
 totals=Counter(r['condition'] for r in rows);best=None
 # Do not examine predictions or choose a split for high model scores.
 for seed in range(42,2042):
  keys=sorted(dates);random.Random(seed).shuffle(keys)
  a=round(len(keys)*.7);b=round(len(keys)*.85)
  parts={'train':keys[:a],'validation':keys[a:b],'test':keys[b:]}
  counts={s:Counter(r['condition'] for k in keys for r in dates[k]) for s,keys in parts.items()}
  if any(counts[s][label]<20 for s in parts for label in totals):continue
  score=sum(abs(counts[s][label]/totals[label]-fraction) for s,fraction in [('train',.7),('validation',.15),('test',.15)] for label in totals)
  if best is None or score<best[0]:best=(score,seed,parts,counts)
 if best is None:raise ValueError('Cannot form date-separated partitions with all conditions represented')
 _,seed,parts,counts=best
 mapping={date:s for s,keys in parts.items() for date in keys}
 for row in rows:row['planned_split']=mapping[row['capture_date']]
 with (OUT/'split_plan.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 report={'seed':seed,'date_partitions':parts,'condition_counts':{s:dict(c) for s,c in counts.items()},
  'policy':'Acquisition dates remain disjoint. Selected on label balance only before training. This plan still requires complete downloads, decoded-image deduplication and visual quality audit. If cross-date duplicates exist, merge their groups and regenerate before training. Do not interpret crop/augmentation counts as independent photographs.'}
 (OUT/'split_plan.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
