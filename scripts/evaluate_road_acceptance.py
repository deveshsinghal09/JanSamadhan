"""Report road acceptance on held-out test data using validation-only thresholds."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'data/image-v4-road-recovery/data'
validation=json.loads((folder/'cascade_validation.json').read_text())
test=json.loads((folder/'cascade_evaluation.json').read_text())
if not test.get('predictions'):
    raise SystemExit('First run: python scripts/evaluate_road_cascade.py --split test')
labels=test['labels']; rows=test['predictions']
scores=np.asarray([r['scores'] for r in rows]); truth=np.asarray([r['truth'] for r in rows])
margin=np.sort(scores,axis=1)[:,-1]-np.sort(scores,axis=1)[:,-2]
result={'policy':'Thresholds chosen on validation only; evaluated once on existing v3 held-out test images, not new external images.','classes':{}}
for label,evidence in validation['acceptance_evidence'].items():
    i=labels.index(label)
    mask=(scores.argmax(1)==i)&(scores[:,i]>=evidence['threshold'])&(margin>=.15)
    actual=truth==i; tp=int((mask&actual).sum()); accepted=int(mask.sum())
    result['classes'][label]={'threshold':evidence['threshold'],'accepted':accepted,'correct':tp,'false_positives':accepted-tp,'precision':tp/accepted if accepted else None,'recall':tp/int(actual.sum()),'test_support':int(actual.sum())}
(folder/'cascade_selective_test.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
