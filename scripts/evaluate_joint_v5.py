"""Post-training report only: never deploy from a single supplied-photo result."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ml.vision import ImageClassifier
run=ROOT/'data/image-v5-joint-run'
metrics=json.loads((run/'data/image_metrics.json').read_text())
baseline=json.loads((ROOT/'data/image_pipeline_metrics.json').read_text())
model=ImageClassifier(run/'ml/image_model.pt')
photo=model.predict((ROOT/'tests/fixtures/external-pothole.jpg').read_bytes())
comparison={label:{'current_f1':baseline['test']['report'][label]['f1-score'],'candidate_f1':metrics['test']['report'][label]['f1-score'],'current_recall':baseline['test']['report'][label]['recall'],'candidate_recall':metrics['test']['report'][label]['recall']} for label in model.labels}
report={'version':model.version,'class_comparison':comparison,'external_photo':photo,'external_expected':'Pothole / broken asphalt','policy':'The user photo was excluded from fitting and checkpoint selection. This diagnostic does not establish generalization. Review all class metrics, source-group results and accepted prediction quality before deployment. No automatic deployment.'}
(run/'data/comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
