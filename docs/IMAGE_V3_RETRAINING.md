# Image model v3 — corrected datasets and measured results

This is the current image-model release. Earlier image-v1/v2 scores describe different datasets and labels and are not directly comparable. The text model and Neon complaint database were not retrained or cleared.

## What changed

The old Road Issues folder-labeled dataset is excluded. Its ordinary signs, weak parking examples and artificial road cutouts are not used in this run. Garbage positives now come from annotated garbage piles and scattered litter, with a visual screening pass on GINI. Isolated plastic-object examples are negative/review examples, not positive garbage incidents. Ordinary signs are never labeled as damaged.

This is supervised MobileNetV3-Small transfer learning from torchvision ImageNet weights. It is a scene classifier, not an object detector or a model trained from scratch.

## Actual dataset counts

9,969 retained labeled image examples in 1,523 source/perceptual groups. 6,944 training, 1,374 validation and 1,651 test examples. These are not all independent photographs: related views and near duplicates are grouped. Online augmentation and resized caches do not add examples.

| Class | Train | Validation | Test | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Garbage / litter | 419 | 80 | 62 | 95.2% | 95.2% | 95.2% |
| Other / review | 154 | 37 | 30 | 88.9% | 80.0% | 84.2% |
| Pothole | 1066 | 209 | 255 | 51.9% | 69.4% | 59.4% |
| Road scene / review | 3104 | 600 | 779 | 81.8% | 72.9% | 77.1% |
| Road surface issue | 1186 | 196 | 311 | 56.3% | 56.3% | 56.3% |
| Streetlight infrastructure | 538 | 165 | 116 | 97.5% | 99.1% | 98.3% |
| Traffic sign / review | 154 | 32 | 36 | 97.3% | 100.0% | 98.6% |
| Waterlogging / flooded road | 323 | 55 | 62 | 100.0% | 98.4% | 99.2% |

Overall test accuracy: **73.59%**. Macro F1: **83.53%**. Do not present these as Lucknow deployment accuracy.

Garbage: 59 of 62 held-out garbage scenes were recognized; there were three missed garbage scenes and three false garbage predictions across the full test set. Road-surface and pothole results are weaker and require review. Streetlight recognition only means that lighting infrastructure is visible. Sign recognition only means a sign is visible.

## Sources and selection

- [SpotGarbage GINI, explicitly annotated photographs](https://github.com/spotgarbage/spotgarbage-GINI): Annotated garbage piles/litter; non-garbage photographs used only as review examples. Local academic use; original image rights remain with creators.
- [RDD2022 India](https://doi.org/10.6084/m9.figshare.21431547.v1): Indian road photographs with PASCAL VOC damage boxes. CC BY-SA 4.0; use labeled training partition only.
- [Roadway Flooding](https://doi.org/10.17632/t395bwcvbw.1): 441 roadway photographs, segmentation masks excluded. CC BY 4.0.
- [Urban Streetlight Analysis](https://github.com/Team16Project/Street-Light-Dataset): Original streetlight photographs. Combined infrastructure class: daytime/off lamps are NOT evidence of electrical failure. Local academic use; no redistribution.
- [TACO](https://github.com/pedropro/TACO): Only photos with at least five annotated litter objects and sufficient annotated area; not isolated-object photographs. Local use; per-photo rights retained.
- [Piles of Garbage](https://www.kaggle.com/datasets/hammadarshad18/garbage-detection): YOLO-annotated garbage piles, Pakistan and web photographs. CC0 listing; overlaps with GINI are deduplicated.
- [Portuguese traffic-sign photographs](https://www.kaggle.com/datasets/danielvareta/damaged-signs-dataset): 500-photo sample. Source labels specify sign type, not condition: used only as Traffic sign / review, never as confirmed damage. CC0 listing.

Retained source counts: RDD2022-India: 7,706, RoadwayFlood: 440, PilesOfGarbage: 273, GINI: 423, Streetlight: 819, SignScenes: 222, TACO: 86.

Only YOLO class 0 from the pile dataset is a garbage positive; bin class 1 is excluded, and isolated-plastic class 2 supplies review negatives. Unlabeled and visually unsuitable GINI positives are excluded. TACO requires at least five annotated objects and at least 4% annotated area. Flood masks are excluded. The sign source supplies 500 full photographs, but only 222 sufficiently sized sign crops remain: one largest annotated sign crop per source photograph. It has no damage-state labels, so its output is Traffic sign / review.

## How training and validation work

Training seed: 42. Group-split seed: 115. Exact pixels, 256-bit perceptual dHash radius 4, source families, TACO acquisition batches, streetlight dates and consecutive RDD ID blocks of 50 stay in a single split. Approximate 70/15/15 group split, selected for label balance only before training. RDD ID blocks are a conservative sequence heuristic, not verified location separation.

Images are resized to a maximum 768-pixel edge in a lossless input cache. Training applies random crops to 224 × 224 pixels, horizontal flips and small colour changes. Validation and testing use deterministic resizing. The cache represents the same examples, not additional images.

The first two epochs train the classifier head with the pretrained CNN frozen. Later epochs fine-tune the CNN with AdamW and class-weighted cross-entropy. Pretrained batch-normalization running statistics remain frozen. Batch size: 32. Up to 16 epochs were allowed; early stopping ended the run after 8 epochs. Epoch 5 had the highest validation macro F1 (84.42%) and was selected before testing. The recorded training/evaluation duration is 101.4 minutes on CUDA, excluding earlier downloads and preparation.

Validation also fits a temperature and acceptance thresholds. The test set is then used to report performance, not choose epochs or thresholds. Temperature minimizes validation negative log likelihood. Garbage/litter and pothole thresholds require >=90% observed validation precision on >=20 accepted validation images, minimum score .70 and top-two margin .15. Other classes always require review. These are in-distribution checks, not guarantees on arbitrary uploads.

Only 106 of 1651 test photos passed the automatic-suggestion gates (6.42% coverage). Accuracy among that small accepted subset was 94.34%; this is not accuracy on all uploads.

Group-weighted evaluation: Each test image receives weight 1 / number of images in its source group. Each group contributes total weight one. Labels remain per image because a road sequence can contain several different conditions.

## Limits you should explain to the panel

- Garbage and waterlogging have useful held-out results, but small class test sets mean uncertainty remains.
- Potholes and cracked roads are difficult in distant road photographs; do not claim reliable automatic routing from those photos.
- A normal sign is not a damaged sign. This model does not diagnose bent, missing, wrong or damaged signs.
- Streetlight infrastructure recognition does not prove a power fault or that a lamp should be on. Electrical faults and household outages are not trained diagnosis classes.
- Illegal parking is not a trained class in this replacement. Legality requires location, signs, timing and officer review.
- Waterlogging is visible standing/flood water, not proof of a blocked sewer or its responsible department.
- There is no independently verified Lucknow image holdout and no guarantee of rejecting arbitrary unrelated images.

## Run and show the code

```powershell
cd "E:\OneDrive\Documents\ChatGPT\JANSAMADHAN"
npm run dev
```

For the built demo use the existing START_DEMO.cmd. The built website is at http://127.0.0.1:3001 and the AI service uses port 8001. Vite development normally uses 5173.

Open **Model & dataset**, then the image section. It reads `data/image_metrics.json`, including per-class precision, recall, F1, confusion matrix, split counts and epoch history. In **Report an issue**, upload a photo and select **Classify attached photo**. Submission recomputes the image result and stores its version with the complaint.

- `ml/prepare_civic_v3.py`: annotation rules, visual exclusions and grouped split.
- `ml/train_images.py`: supervised training, checkpoint selection, calibration and evaluation.
- `ml/vision.py`: image decoding, inference and review decisions.
- `ml/service.py`: `/predict-image`; reloads a replaced checkpoint on the next request.
- `frontend/ImageModel.jsx`: results and model evidence display.
- `data/images/manifest.csv`: exact source paths, labels, splits, group IDs and hashes.
- `data/images/v3-sources/audit/`: local visual audit sheets; not redistributed.
- `data/images/archive/pre-v3-release/`: previous release backup.

To reproduce with the downloaded source data: `npm run train:images`. This writes a separate candidate under `data/image-v3-run`; it does not silently overwrite the deployed model. `scripts/promote_image_v3.py` verifies a completed run and retains the previous release before installation.

The Word report produced before this retraining still contains historical v2 image results. Use this guide and the live metrics for the new image experiment.
