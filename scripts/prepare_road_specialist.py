"""Preserve v3 source groups and splits for a higher-resolution road experiment."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'data/images/manifest.csv'
out=ROOT/'data/images/v4-road-prepared'
out.mkdir(parents=True,exist_ok=True)
with source.open(encoding='utf8') as f:
    rows=[r for r in csv.DictReader(f) if r['source']=='RDD2022-India']
assert rows and {r['split'] for r in rows}=={'train','validation','test'}
groups={s:{r['group'] for r in rows if r['split']==s} for s in ('train','validation','test')}
assert not groups['train'] & (groups['validation']|groups['test'])
assert not groups['validation'] & groups['test']
with (out/'manifest.csv').open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
audit=json.loads((ROOT/'data/images/audit.json').read_text())
audit.update(retained_images=len(rows),groups=len(set(r['group'] for r in rows)),
    class_counts={s:dict(Counter(r['label'] for r in rows if r['split']==s)) for s in groups},
    source_counts=dict(Counter(r['source'] for r in rows)),
    label_policy='RDD2022 India XML annotations: D40 potholes; D00/D10/D20 road surface damage; remaining frames road scene/review. Unchanged v3 group split. Multiple annotated defects can coexist; the whole-frame label prioritizes potholes.',
    limitations='Road-only experimental classifier. Must be gated by a civic-scene classifier before use on arbitrary uploads. Normal here means no target damage annotation, not independently verified absence of all defects. No verified Lucknow holdout. Existing test set was previously evaluated by v3; it is a regression benchmark, not a newly unseen external test set.')
audit['sources']=[s for s in audit['sources'] if s['name']=='RDD2022 India']
(out/'audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'images':len(rows),'splits':audit['class_counts']},indent=2))
