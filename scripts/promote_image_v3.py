"""Verify and install a completed checkpoint, preserving the previous release."""
import csv,hashlib,json,shutil,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'data/image-v3-run'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 metrics=json.loads((RUN/'data/image_metrics.json').read_text())
 assert metrics['modelVersion']=='image-v3'
 assert digest(RUN/'ml/image_model.pt')==metrics['model_sha256']
 assert digest(RUN/'data/images/manifest.csv')==metrics['manifest_sha256']
 rows=list(csv.DictReader((RUN/'data/images/manifest.csv').open(encoding='utf8')))
 assert len(rows)==metrics['audit']['retained_images']
 for key in ('group','source_family','pixel_hash','sha256','dhash'):
  assigned={}
  for row in rows:assert assigned.setdefault(row[key],row['split'])==row['split'],key
 # This gate is a release check, not a reason to tune repeatedly on the test set.
 assert metrics['test']['report']['Garbage / litter']['recall']>=.8
 assert metrics['test']['report']['Garbage / litter']['precision']>=.8
 backup=ROOT/'data/images/archive/pre-v3-release';backup.mkdir(parents=True,exist_ok=True)
 files=['ml/image_model.pt','data/image_metrics.json','data/images/manifest.csv','data/images/audit.json','data/images/training_history.json']
 for rel in files:
  source=ROOT/rel;target=backup/rel
  if source.exists() and not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 for rel in files:
  source=RUN/rel;target=ROOT/rel;temporary=target.with_name(target.name+'.new')
  shutil.copy2(source,temporary);os.replace(temporary,target)
 print('Installed image-v3; previous release retained in',backup)
