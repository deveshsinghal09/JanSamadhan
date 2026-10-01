# Pothole detector readiness

Prepared a detector-ready RDD-only dataset with original D40 bounding boxes:
- Train: 5,356 images / 2,228 pothole boxes.
- Validation: 1,005 images / 428 boxes.
- Test: 1,345 images / 531 boxes.

Images with no D40 annotation act as road-background examples. Other civic sources are excluded because their presumed absence of potholes was not verified. Existing source groups and splits are unchanged. The supplied Newport photo is excluded.

Preparation: scripts/build_pothole_detector_layout.py. Configuration: data/images/pothole-detector-rdd/dataset.yaml. Audit: data/images/pothole-detector-rdd/audit.json. Images use hard links to existing data without new downloads.

Training runner: scripts/train_pothole_detector.py. Proposed run: COCO-pretrained YOLOv8n, 640px, batch 4, 40 maximum epochs, patience 7, seed 42. It evaluates the validation-selected checkpoint on the held-out test split and then the external photo; it never automatically deploys. Detection mAP is not classification accuracy. Non-road false positives must also be evaluated before integration.

Both scripts compile. Detector training has NOT started: ultralytics is not installed. The previous installation was rejected by automatic approval review due to a usage limit, with retry time 6:59 PM. At this turn's check, local time was 6:30 PM. The installation was not retried or bypassed. Current website remains image-v4-road.

## Training launch

The explicit installation retry was approved and ultralytics 8.4.149 installed successfully. GPU training was launched using scripts/train_pothole_detector.py, with output in data/pothole-training.log and data/pothole-training-error.log. Maximum 40 epochs, patience 7, batch 4, 640px; mixed precision disabled for stable execution. External experiment logging integrations are disabled. This launch supersedes the earlier installation-blocked status; results are not yet available.
