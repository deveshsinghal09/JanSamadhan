"""Generate the review guide from the installed, measured experiment."""
import csv,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'data/image_metrics.json').read_text())
rows=list(csv.DictReader((ROOT/'data/images/manifest.csv').open(encoding='utf8')))
lines=['# Image model v3 — corrected datasets and measured results','',
'This is the current image-model release. Earlier image-v1/v2 scores describe different datasets and labels and are not directly comparable. The text model and Neon complaint database were not retrained or cleared.', '',
'## What changed','',
'The old Road Issues folder-labeled dataset is excluded. Its ordinary signs, weak parking examples and artificial road cutouts are not used in this run. Garbage positives now come from annotated garbage piles and scattered litter, with a visual screening pass on GINI. Isolated plastic-object examples are negative/review examples, not positive garbage incidents. Ordinary signs are never labeled as damaged.', '',
'This is supervised MobileNetV3-Small transfer learning from torchvision ImageNet weights. It is a scene classifier, not an object detector or a model trained from scratch.', '',
'## Actual dataset counts','',
f"{m['audit']['retained_images']:,} retained labeled image examples in {m['audit']['groups']:,} source/perceptual groups. {m['splits']['train']:,} training, {m['splits']['validation']:,} validation and {m['splits']['test']:,} test examples. These are not all independent photographs: related views and near duplicates are grouped. Online augmentation and resized caches do not add examples.", '',
'| Class | Train | Validation | Test | Precision | Recall | F1 |','|---|---:|---:|---:|---:|---:|---:|']
for label in m['test']['labels']:
 r=m['test']['report'][label];counts=[sum(x['label']==label and x['split']==s for x in rows) for s in ['train','validation','test']]
 lines.append('| '+label+' | '+' | '.join(str(x) for x in counts)+f" | {r['precision']:.1%} | {r['recall']:.1%} | {r['f1-score']:.1%} |")
lines+=['',f"Overall test accuracy: **{m['test']['report']['accuracy']:.2%}**. Macro F1: **{m['test']['report']['macro avg']['f1-score']:.2%}**. Do not present these as Lucknow deployment accuracy.", '',
'Garbage: 59 of 62 held-out garbage scenes were recognized; there were three missed garbage scenes and three false garbage predictions across the full test set. Road-surface and pothole results are weaker and require review. Streetlight recognition only means that lighting infrastructure is visible. Sign recognition only means a sign is visible.', '',
'## Sources and selection','']
for s in m['sources']:lines.append(f"- [{s['name']}]({s['url']}): {s['scope']}")
lines+=['','Retained source counts: '+', '.join(f'{k}: {v:,}' for k,v in m['audit']['source_counts'].items())+'.', '',
'Only YOLO class 0 from the pile dataset is a garbage positive; bin class 1 is excluded, and isolated-plastic class 2 supplies review negatives. Unlabeled and visually unsuitable GINI positives are excluded. TACO requires at least five annotated objects and at least 4% annotated area. Flood masks are excluded. The sign source supplies 500 full photographs, but only 222 sufficiently sized sign crops remain: one largest annotated sign crop per source photograph. It has no damage-state labels, so its output is Traffic sign / review.', '',
'## How training and validation work','',
f"Training seed: {m['seed']}. Group-split seed: {m['audit']['split_seed']}. {m['audit']['split_policy']}", '',
'Images are resized to a maximum 768-pixel edge in a lossless input cache. Training applies random crops to 224 × 224 pixels, horizontal flips and small colour changes. Validation and testing use deterministic resizing. The cache represents the same examples, not additional images.', '',
f"The first two epochs train the classifier head with the pretrained CNN frozen. Later epochs fine-tune the CNN with AdamW and class-weighted cross-entropy. Pretrained batch-normalization running statistics remain frozen. Batch size: 32. Up to 16 epochs were allowed; early stopping ended the run after {m['epochs_run']} epochs. Epoch {m['best_epoch']} had the highest validation macro F1 ({max(h['validation_macro_f1'] for h in m['history']):.2%}) and was selected before testing. The recorded training/evaluation duration is {m['training_seconds']/60:.1f} minutes on CUDA, excluding earlier downloads and preparation.", '',
'Validation also fits a temperature and acceptance thresholds. The test set is then used to report performance, not choose epochs or thresholds. '+m['calibration']['policy'], '',
f"Only {m['selective_test']['accepted']} of {m['splits']['test']} test photos passed the automatic-suggestion gates ({m['selective_test']['coverage']:.2%} coverage). Accuracy among that small accepted subset was {m['selective_test']['precision']:.2%}; this is not accuracy on all uploads.", '',
'Group-weighted evaluation: '+m['group_evaluation'], '',
'## Limits you should explain to the panel','',
'- Garbage and waterlogging have useful held-out results, but small class test sets mean uncertainty remains.',
'- Potholes and cracked roads are difficult in distant road photographs; do not claim reliable automatic routing from those photos.',
'- A normal sign is not a damaged sign. This model does not diagnose bent, missing, wrong or damaged signs.',
'- Streetlight infrastructure recognition does not prove a power fault or that a lamp should be on. Electrical faults and household outages are not trained diagnosis classes.',
'- Illegal parking is not a trained class in this replacement. Legality requires location, signs, timing and officer review.',
'- Waterlogging is visible standing/flood water, not proof of a blocked sewer or its responsible department.',
'- There is no independently verified Lucknow image holdout and no guarantee of rejecting arbitrary unrelated images.', '',
'## Run and show the code','',
'```powershell\ncd "E:\\OneDrive\\Documents\\ChatGPT\\JANSAMADHAN"\nnpm run dev\n```', '',
'For the built demo use the existing START_DEMO.cmd. The built website is at http://127.0.0.1:3001 and the AI service uses port 8001. Vite development normally uses 5173.', '',
'Open **Model & dataset**, then the image section. It reads `data/image_metrics.json`, including per-class precision, recall, F1, confusion matrix, split counts and epoch history. In **Report an issue**, upload a photo and select **Classify attached photo**. Submission recomputes the image result and stores its version with the complaint.', '',
'- `ml/prepare_civic_v3.py`: annotation rules, visual exclusions and grouped split.',
'- `ml/train_images.py`: supervised training, checkpoint selection, calibration and evaluation.',
'- `ml/vision.py`: image decoding, inference and review decisions.',
'- `ml/service.py`: `/predict-image`; reloads a replaced checkpoint on the next request.',
'- `frontend/ImageModel.jsx`: results and model evidence display.',
'- `data/images/manifest.csv`: exact source paths, labels, splits, group IDs and hashes.',
'- `data/images/v3-sources/audit/`: local visual audit sheets; not redistributed.',
'- `data/images/archive/pre-v3-release/`: previous release backup.', '',
'To reproduce with the downloaded source data: `npm run train:images`. This writes a separate candidate under `data/image-v3-run`; it does not silently overwrite the deployed model. `scripts/promote_image_v3.py` verifies a completed run and retains the previous release before installation.', '',
'The Word report produced before this retraining still contains historical v2 image results. Use this guide and the live metrics for the new image experiment.']
(ROOT/'docs/IMAGE_V3_RETRAINING.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print('Wrote docs/IMAGE_V3_RETRAINING.md')
