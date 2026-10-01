> Current image release: image-v3. See [corrected datasets and measured results](IMAGE_V3_RETRAINING.md). Image-v1/v2 figures below are historical; live metrics are in data/image_metrics.json.

> Image-model correction: see [IMAGE_V2_FIX.md](IMAGE_V2_FIX.md) for the roadside-garbage coverage fix and current limitations. Older image-v1 results below are historical; current metrics are in data/image_metrics.json.

# Image classification — faculty review guide

## What this component does

The image model is a separate convolutional neural network. It looks at an uploaded photograph and predicts a visual scene class. Image results may identify waste materials or visible road features but do not alone establish a civic fault. The text model still suggests the department and priority. The application stores both predictions, displays agreement/disagreement and keeps an officer action history. Image results are advisory, not proof of an incident or authority to contact a department.

The seven visual classes are **Waste material, Pothole, Road surface issue, Damaged road sign, Graffiti, Parking scene and Street scene / review**. The original folder names are adapted to avoid overclaiming: a photo of parked vehicles does not prove illegal parking, and the road-surface folder includes speed breakers as well as damage. Water-supply failure, sewer blockage and streetlight functionality are **not trained image classes**. A single daytime photo cannot reliably establish those conditions.

## Dataset and provenance

Source: [Road Issues Detection Dataset on Kaggle](https://www.kaggle.com/datasets/programmerrdai/road-issues-detection-dataset), credited to the OutlierRejects team: Ranuga Disansa, Sanila Wijesekara, Thuan Naheem and Rivindu Ashinsa. The downloaded archive contains 9,660 JPEG files:

| Source folder | Files |
|---|---:|
| Pothole Issues | 3,348 |
| Vandalism Issues | 2,128 |
| Broken Road Sign Issues | 1,793 |
| Littering Garbage on Public Places Issues | 1,419 |
| Damaged Road issues | 677 |
| Illegal Parking Issues | 104 |
| Mixed Issues | 191 |

A spot-check found ordinary street scenes in the litter folder. We therefore relabel that entire folder **Street scene / review**, with no garbage-routing implication. We add 2,527 original [TrashNet](https://github.com/garythung/trashnet) images from Gary Thung and Mindy Yang and collapse glass, paper, cardboard, plastic, metal and trash into **Waste material**. Their MIT repository license is preserved. These objects are photographed on a white background: this introduces a strong source/background shortcut and does not establish street dumping. The combined raw input contains 12,187 images before filtering.

Images with more than 18% near-black pixels in a 64 × 64 thumbnail are removed because source augmentations include severe black cutout. This also reduces dark/night coverage, which is a limitation. No claim of full manual annotation review is made.

The mixed folder is excluded because this is a single-label classifier. Corrupt, tiny, duplicate and conflicting-group images are removed before training. The audit retained **10,814 images in 6,551 groups**: **7,564 train / 1,639 validation / 1,611 test**. It removed 4 exact same-label duplicates, 992 heavily black/occluded images, 191 mixed-label images and 186 images in conflicting groups. The actual retained counts and final split sizes are generated in `data/images/audit.json` and `data/image_metrics.json`; the website reads them directly. Do not call 9,660 the number used in training or the number of independent original scenes.

The publisher describes a compilation of Roboflow/Kaggle/Mendeley sources. It is not a verified Indian-state or Lucknow collection. Its metadata says MIT while its description says CC0; upstream images may have separate conditions. We preserve the exact publisher metadata in `data/images/programmerrdai.json`, disclose the ambiguity, and exclude the raw images/archive from the shareable review ZIP. Local academic experimentation is not evidence of cleared redistribution/commercial rights. Confirm upstream permissions before public deployment or dataset redistribution. Downloading did not require sending personal data or accepting a separate agreement.

## Why transfer learning?

Training a CNN from random weights needs more varied, independently labelled data than this collection provides. MobileNetV3-Small already has useful ImageNet visual features such as edges, shapes and textures. We replace its final classification layer with seven outputs and train on civic images.

The initial ImageNet weights come from [official torchvision MobileNetV3-Small](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html). Those pretrained weights are not our own training result. The saved civic checkpoint contains weights updated by this project's training run. This is supervised transfer learning, not an LLM image call, not object detection and not a model trained from scratch.

## Training pipeline

1. Decode and validate the source files, hash their original bytes and decoded pixels, and record folder labels.
2. Group versions sharing an original filename before the `.rf.` augmentation suffix. Group same-location `_A1`, `_A2` viewpoints, exact pixels and perceptually close difference hashes (64 bits, Hamming distance at most four). Connected matches stay together.
3. Exclude groups that disagree on labels. Split remaining groups by category with seed 42: approximately 70% train, 15% validation and 15% test. Image percentages can differ because groups have different sizes.
4. Resize input to 224 × 224 RGB and use ImageNet normalization. Training additionally uses random crops, horizontal flips and small brightness/contrast/color changes. Evaluation uses deterministic resizing. Augmentation increases variation, not the independent sample count.
5. Train the new classifier for two epochs with frozen CNN features. Then fine-tune the complete CNN with a smaller learning rate. Use class-weighted cross-entropy and AdamW. Batch size 32; at most eight epochs; stop after three non-improving validation epochs after the initial warm-up.
6. Save the checkpoint with the best validation macro F1. Evaluate the held-out test split only after checkpoint selection. Save per-class precision, recall, F1, support, confusion matrix and the complete epoch history.

Hyperparameters: classifier warm-up learning rate 0.001; fine-tuning CNN learning rate 0.00005 and classifier 0.0003; weight decay 0.01. Class weights are calculated from training counts only. The RTX 3050 GPU is used when available; inference runs on CPU for a lightweight local service. Exact reproducibility across different GPU libraries/hardware is not guaranteed by a fixed seed.

## Questions the faculty may ask

**Is it classification or detection?** Classification: one label for the whole image. It does not draw bounding boxes, count potholes or locate defects. Object detection would need verified bounding-box annotations and a separately evaluated detector.

**How do you avoid train/test leakage?** Group source versions and perceptual matches before splitting. Automated tests check family, pixel hash, file hash and near-difference-hash isolation. These heuristics cannot guarantee isolation of every semantic near-duplicate, video sequence or changed viewpoint.

**Why not show accuracy alone?** Class frequencies are uneven; parking has very little support. Macro F1 gives each class equal weight. Per-class recall shows missed defects, precision shows false alerts, and the confusion matrix shows which classes are mixed up.

**Can it recognize an unrelated selfie or a healthy road?** The Street scene / review class is a limited review class, not a validated universal normal/unknown detector. Softmax always distributes probability over known labels. A 70% review threshold catches some uncertain images, but even an unrelated image can receive a high score. The interface discloses this. Robust unknown-image rejection requires a separate negative corpus and evaluation.

**Does a confident image decide the department?** No. It provides a suggested visual category. The text model and jurisdiction guards propose routing; disagreement remains visible for the officer. Waste material may support Sanitation and potholes may support Engineering, subject to asset ownership. Other visual classes remain manually reviewed.

**Does it estimate urgency?** No image severity model is trained. The existing text priority model remains separate and officers can correct it with an explanation.

**Is this validated for Lucknow?** No. The project uses Lucknow routing, but the external image collection has mixed origins. A local, independent, consented test set is still needed.

## Reproduce and demonstrate

Dependencies are installed in the project virtual environment. `TRAIN_IMAGES.cmd` downloads the source archive if missing and starts training. `npm run train:images` trains when the archive is already present. First-time training needs Internet for source images and official pretrained weights. The review package includes the final civic model, manifest, audit and metrics; normal inference uses no online AI service.

After retraining, restart the AI process to load new weights. Do not claim new weights are active merely because a new file exists on disk.

In the app, open Report an issue, attach a PNG/JPEG (at least 32 × 32 pixels, at most 3 MB) and click **Classify attached photo**. Inspect the visual class, score and limits. Analyze the written description, submit, and open the report to show the saved photo result. Submission recomputes the image prediction; the browser cannot supply a forged result. Invalid/truncated images are rejected. Displayed scores are uncalibrated model probabilities.

Open **Model & dataset** and scroll to the image-model section for the measured results, epoch history, split counts and confusion matrix. Practice explaining one correct classification and one failure from the held-out results instead of selecting only successful examples.

## Selected training stage

The final checkpoint is selected by validation macro F1, not by whether its backbone is trainable. If the best epoch is 1 or 2, deployment uses frozen ImageNet CNN features with a locally trained classifier head. If it is later, deployment uses the fine-tuned backbone. The run still evaluates both strategies; do not describe a selected frozen-backbone model as a fully fine-tuned CNN. The website explicitly displays the selected stage.

## Measured results — completed run

Five epochs ran; early stopping retained epoch 2 (validation macro F1 86.8%). The deployed model uses a frozen ImageNet backbone and a locally trained classifier head. Full CNN fine-tuning was tried in epochs 3–5 and did not outperform it.

Test image accuracy: **93.6%**; macro F1: **85.1%**, on **1,611 images**. One vote per source/perceptual group: accuracy **95.5%**, macro F1 **85.4%**, on **983 groups**. These are external dataset results, not Lucknow deployment performance.

| Visual class | Test F1 | Test images |
|---|---:|---:|
| Damaged road sign | 96.4% | 260 |
| Graffiti | 93.3% | 271 |
| Parking scene | 60.9% | 12 |
| Pothole | 93.9% | 430 |
| Road surface issue | 58.0% | 68 |
| Street scene / review | 95.0% | 213 |
| Waste material | 98.2% | 357 |

Road-surface and parking recognition are weak and have limited support. Waste-material results benefit from studio backgrounds; do not interpret them as validated street-garbage detection. The classifier has 1525031 parameters. Training/evaluation took 783.4 seconds after data preparation, excluding dependency downloads.

Local demo photos are under `data/images/demo/`; source selections are recorded there. They and the raw archives are excluded from the review ZIP. Use your own relevant photo or download the source data on another computer.
