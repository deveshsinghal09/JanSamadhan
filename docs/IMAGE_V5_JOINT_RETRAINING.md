# Joint image retraining v5

The Newport pothole failure reproduced at 84.42% waterlogging under image-v4-road. The base classifier assigns almost no road probability, which the gated road specialist cannot recover. The specialist alone also confuses pothole with generic road damage.

A new joint eight-class MobileNetV3-Large run now learns road, flood and other civic scenes together, without that gate. It uses ImageNet-pretrained weights, 384px full-frame resize, train-only flip/color jitter, class-weighted cross entropy, two head warm-up epochs followed by full fine-tuning, and best validation macro F1 checkpoint selection. Maximum 16 epochs; early stopping after three stale epochs once eligible. Existing audited source groups and train/validation/test assignments are preserved.

Counts: 9,969 total; 6,944 train, 1,374 validation, 1,651 test. Potholes 1,530; road surface issues 1,693; road scenes 4,483; flooded roads 440; garbage 561; other 221; streetlight infrastructure 819; sign scenes 222. These include grouped variants, not 9,969 independent scenes. This run does not solve damaged signs, parking or electrical defects.

The user-supplied photograph is excluded from training and checkpoint selection. Its hash was checked against the manifest. It remains an external diagnostic, not an external benchmark. No new images were downloaded for this run; improved performance is an experiment, not guaranteed.

Runner: scripts/train-joint-v5.ps1. Output: data/training-v5.log. Errors: data/training-v5-error.log. Candidate artifacts: data/image-v5-joint-run. Post-training comparison: data/image-v5-joint-run/data/comparison.json. The runner automatically evaluates the supplied photograph and compares held-out per-class scores after training. It does not automatically deploy.

Training was confirmed on CUDA. Website remains on image-v4-road with text/photo disagreement review. Electrical recovery stopped after five completed epochs without a final metrics report; parking did not start. Their saved artifacts are preserved. The reported pothole recognition problem is being prioritized.
