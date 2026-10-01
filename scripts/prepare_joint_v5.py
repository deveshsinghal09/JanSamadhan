"""Prepare the joint civic retraining run without changing any data split."""
import csv,hashlib,json,shutil
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'data/images/v5-joint-prepared';out.mkdir(parents=True,exist_ok=True)
source=root/'data/images/manifest.csv'
with source.open(encoding='utf8') as f:rows=list(csv.DictReader(f))
external=root/'tests/fixtures/external-pothole.jpg'
assert hashlib.sha256(external.read_bytes()).hexdigest() not in {r['sha256'] for r in rows}
for key in ('group','source_family','pixel_hash','sha256'):
 assigned={}
 for r in rows:
  if assigned.setdefault(r[key],r['split'])!=r['split']:raise ValueError('Split leakage: '+key)
audit=json.loads((root/'data/images/audit.json').read_text())
audit['experiment']='Joint eight-class MobileNetV3-Large; all scene scores learned together, no base-model road gate.'
audit['limitations']+=' Existing v3 partitions are reused. The supplied Newport pothole is an external diagnostic excluded from fitting and checkpoint selection; it is not representative of an external benchmark.'
shutil.copy2(source,out/'manifest.csv');(out/'audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'images':len(rows),'splits':dict(Counter(r['split'] for r in rows)),'classes':dict(Counter(r['label'] for r in rows)),'external_photo_in_training':False},indent=2))
