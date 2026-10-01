import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ml.clip_classifier import ClipClassifier
model=ClipClassifier(ROOT/'data/image-v6-clip-run/classifier.joblib')
r=model.predict((ROOT/'tests/fixtures/external-pothole.jpg').read_bytes())
(ROOT/'data/image-v6-clip-run/external_pothole.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
