> Current image release: image-v3. See [corrected datasets and measured results](IMAGE_V3_RETRAINING.md). Image-v1/v2 figures below are historical; live metrics are in data/image_metrics.json.

# Roadside garbage failure: diagnosis and image-v2 correction

## Completed training and live deployment — 9 September 2026

Image-v2 is now the live checkpoint. The cleaned dataset contains 12,189 images: 8,495 training, 1,906 validation and 1,788 test images. Eight epochs completed; validation macro F1 selected epoch 7. Held-out test accuracy is 92.8% and macro F1 is 83.0%. The review policy accepted 899 of 1,788 test images (50.3% coverage), with 96.4% precision among accepted suggestions.

On the same 182 held-out TACO litter photos, litter recall rose from 15.9% for v1 to 98.4% for v2. This measures recognition of litter only, not false positives or performance on all Lucknow complaints. A large outdoor-litter photo was also classified and saved through the live website. The exact original user photo remains unavailable for a direct regression check.

## What failed

A citizen reported that a roadside garbage photo received `Parking scene` with an 84.5% model score. The exact photo was not included in the chat, so this example cannot yet be claimed as a reproduced regression test.

The v1 experiment had a serious coverage gap: its `Waste material` examples came from TrashNet, mostly isolated objects on plain backgrounds. Roadside garbage has pavement, vehicles, vegetation, shadows and small objects. High held-out accuracy on the original source mixture did not establish performance on these scenes. Softmax always chooses among the known labels and can confidently choose the wrong one.

## Changes

- Add official annotated TACO photos with litter in real environments; use the published 640-pixel URLs. Do not label arbitrary unlabeled photos as garbage.
- Combine these and TrashNet into `Garbage / litter`. This class describes visible material; it does not prove illegal dumping or a service failure.
- Keep the original road dataset's ambiguous litter folder as `Street scene / review`. Its folder name alone is not reliable incident annotation.
- Group TACO by acquisition batch as well as the existing source/hash grouping, and stratify it separately. Related capture sequences stay in one split. Reject conflicting-label groups.
- Retrain MobileNetV3-Small from ImageNet initialization, with classifier warm-up and full fine-tuning candidates. Keep batch-normalization running statistics fixed for stability. Select the checkpoint by validation macro F1.
- Fit one temperature using validation negative log likelihood. Temperature changes the score distribution, not which class wins.
- Permit an automatic visual suggestion only for garbage/litter or potholes when the validation-derived threshold and a 0.15 top-two score margin are met. Threshold selection requires at least 20 accepted validation images and at least 90% observed validation precision. This is not a guarantee on new photos.
- Keep parking, graffiti, road signs, road-surface issues and street-review predictions in manual review. A single photo cannot establish parking legality; weak road-surface performance is not hidden by a high overall accuracy.
- Display `Photo needs review` for uncertain results. The actual top class and every model score remain accessible under model details. No text keywords overwrite the image prediction.
- Continue to derive department routing from the complaint description. Photo disagreement remains available for officer review.

## How evaluation works

The model is trained in `data/image-v2-run` before replacing the live checkpoint. The previous model, metrics and manifest are preserved in `data/images/archive/image-v1`.

`scripts/evaluate_image_upgrade.py` compares both checkpoints on the same held-out TACO acquisition batches. Report litter recall here, and use the overall confusion matrix to assess false positives and other categories. The old and new overall datasets differ; their overall accuracy values are not a paired improvement claim.

The precise run counts, metrics, class reports, calibration policy and outdoor-litter comparison are in `data/image_metrics.json` and the website's Model & dataset page. Training can be run with `.venv\Scripts\python.exe -m ml.train_images --epochs 8 --run-dir data/image-v2-run --version image-v2` after installing requirements-images.txt and preparing the source image datasets. Raw source photos are excluded from the review ZIP and must be downloaded separately. The TRAIN_IMAGES.cmd launcher is excluded because Windows security blocked it during packaging; GPU availability changes runtime. Download failures and source URLs are recorded in `data/images/taco_download.json`.

## Scope you can explain to the panel

“We identified a domain gap between isolated waste-object training photos and outdoor complaints. We added contextual litter data, kept acquisition batches out of training for evaluation, compared the old and new models on identical unseen litter photos, and added an abstention policy for uncertain results. We still need a separately collected Lucknow test set before claiming local reliability.”

This remains a single-label scene classifier. A photo may contain several issues or an issue too small to recognize after resizing. It does not detect boxes, identify every municipal category, verify location, infer urgency, establish a blocked underground sewer, or determine whether a streetlight works. Taking a clear closer photo and supplying a description helps the officer; it is not a promise that all photos will classify correctly.

## Sources and rights

- TACO, Pedro F. Proença and Pedro Simões: https://github.com/pedropro/TACO ; paper https://arxiv.org/abs/2003.06975 . The downloaded official annotations include missing per-photo license values. Keep photos local and exclude them from the review package; do not claim blanket redistribution clearance.
- TrashNet, Gary Thung and Mindy Yang: https://github.com/garythung/trashnet . Studio-background limitations remain relevant.
- Original road data: https://www.kaggle.com/datasets/programmerrdai/road-issues-detection-dataset . Listing/description license discrepancy and heterogeneous upstream provenance remain unresolved.

No public upload of these training photos or government complaint submission is part of this correction.
