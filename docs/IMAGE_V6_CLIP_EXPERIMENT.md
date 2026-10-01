# CLIP civic classifier experiment

The CNN failure on the supplied Newport pothole persisted after joint retraining. This experiment uses OpenAI CLIP ViT-B/32 as a frozen feature encoder, then fits a supervised multinomial Logistic Regression classifier on the same 6,944 training images. Regularization C in {0.1, 1, 10, 100} and semantic blending weight in {0, .25, .5, .75, 1} are evaluated on 1,374 validation images. The selection criterion is validation macro F1. Validation also sets temperature and acceptance thresholds. The 1,651-image test set and supplied photo are not used to fit the head or select these settings.

Descriptions for eight classes are fixed in ml/clip_features.py before evaluation (two per class, three for Other). Blending combines normalized log probabilities from the supervised head and image/text similarity. It does not use the citizen's description; complaint text is combined separately by backend/evidence.js.

These are frozen-feature classifier fits, not additional CNN training epochs. The CLIP encoder is pretrained, not trained from scratch by this project. Source: https://huggingface.co/openai/clip-vit-base-patch32 . Pinned revision is stored in data/clip-pretrained/revision.txt. No complaint photos are uploaded.

Feature caches preserve the original source-group splits. The existing test set has been evaluated in earlier experiments and is not a fresh external benchmark. The supplied photo is a diagnostic, not evidence of general accuracy. Deployment requires reviewing per-class results and actual image prediction.

The supplied photograph is excluded from project-specific supervised fitting and model selection. Its possible presence in CLIP's original web pretraining corpus is unknown. It must not be called a proven unseen image relative to pretraining.

## Continued diagnosis and detector preparation

Validation selected a frozen-CLIP supervised scene gate plus the existing road specialist (semantic weight 0, road weight 1). Its existing-test macro F1 is 0.88632, but this alone does not establish a fix for the supplied photo. Semantic-only validation macro F1 is only 0.53173. Results are in gating_comparison.json.

Nearest training images to the supplied photo were inspected visually in nearest-training.jpg. Most are genuine flooded scenes; there is no basis to relabel them as potholes. This suggests appearance/source-domain bias rather than a demonstrated batch of wrong flood labels.

Prepared original RDD D40 bounding-box labels for detector work: 6,252 training images / 2,228 boxes; 1,177 validation images / 428 boxes; 1,499 test images / 531 boxes. Existing source-group splits are retained. Non-RDD garbage/flood/other images are provisional negatives and need inspection before training because missing boxes do not prove absence of potholes. This is preparation, not trained detection. Script: scripts/prepare_pothole_detection.py; audit: data/images/pothole-detection-prepared/audit.json.

Automatic approval review rejected installation of ultralytics, reporting a Codex usage limit and a retry time of 6:59 PM. The rejected installation was not bypassed or retried by another route. Local evaluation and annotation preparation proceeded. Current deployed model remains image-v4-road; the actual photo-recognition failure is unresolved.
