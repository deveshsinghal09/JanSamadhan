"""Publish tested road refinement; preserve the original base checkpoint/report."""
import copy,hashlib,json,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
base=read('data/image_metrics.json')
road=read('data/image-v4-road-recovery/data/image_metrics.json')
test=read('data/image-v4-road-recovery/data/cascade_evaluation.json')
val=read('data/image-v4-road-recovery/data/cascade_validation.json')
assert sha(ROOT/'ml/image_model.pt')==base['model_sha256']
source=ROOT/'data/image-v4-road-recovery/ml/image_model.pt'
assert sha(source)==road['model_sha256']
assert len(test['predictions'])==base['splits']['test']
thresholds=dict(base['calibration']['class_thresholds'])
thresholds['Pothole']=val['acceptance_evidence']['Pothole']['threshold']
thresholds['Road surface issue']=1.01
config={'version':'image-v4-road','road_model':'ml/image_road_model.pt','class_thresholds':thresholds,'metrics':'data/image_pipeline_metrics.json'}
report=copy.deepcopy(base)
report.update(modelVersion=config['version'],architecture='MobileNetV3-Small + MobileNetV3-Large road refinement',test={'labels':test['labels'],'report':test['cascade_report'],'confusion_matrix':test['cascade_confusion_matrix']},test_group_report=test['group_weighted_report'])
report['pipeline']={'description':'The base civic classifier identifies scene types. A road specialist redistributes only the road scores; non-road scores remain unchanged.','base_version':base['modelVersion'],'road_version':road['modelVersion'],'road_model_sha256':road['model_sha256'],'road_history':road['history'],'road_best_epoch':road['best_epoch'],'road_splits':road['splits'],'road_training':road['training'],'evaluation':'Combined results use the existing 1,651-image v3 test set, not a new external Lucknow test. Road training images are a subset of the base corpus, not additional unique images.'}
report['calibration']['class_thresholds']=thresholds
report['calibration']['policy']='Base temperature applies to base scores; the road specialist uses its own validation-fitted temperature. Pothole threshold selected using combined validation predictions, minimum .70 score, .15 margin and 90% precision on at least 20 accepted images. Surface issues and unsupported classes remain manual review.'
report['pipeline']['road_temperature']=road['calibration']['temperature']
scores=np.array([r['scores'] for r in test['predictions']]); truth=np.array([r['truth'] for r in test['predictions']]); predictions=scores.argmax(1)
mask=np.array([test['labels'][p] in ('Garbage / litter','Pothole') and scores[i,p]>=thresholds[test['labels'][p]] and np.sort(scores[i])[-1]-np.sort(scores[i])[-2]>=.15 for i,p in enumerate(predictions)])
report['selective_test']={'accepted':int(mask.sum()),'coverage':float(mask.mean()),'precision':float((predictions[mask]==truth[mask]).mean()) if mask.any() else None}
report['limitations']+=' Road refinement increases pothole F1 but misses some potholes; test acceptance recall for potholes is 41.6%. Sign, electrical and parking defect specialists are not deployed in this pipeline.'
shutil.copy2(source,ROOT/config['road_model'])
(ROOT/config['metrics']).write_text(json.dumps(report,indent=2))
# Config is the last write: the service can now load both complete artifacts.
configpath=ROOT/'ml/image_pipeline.json';temp=configpath.with_suffix('.tmp');temp.write_text(json.dumps(config,indent=2));temp.replace(configpath)
print(json.dumps({'version':config['version'],'selective_test':report['selective_test']},indent=2))
