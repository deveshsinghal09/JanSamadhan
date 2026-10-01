# Image v4 recovery status — 12 September 2026

The earlier terminal sessions ended before electrical evaluation and before parking training began. The electrical candidate had completed four epochs; its best saved validation macro F1 was 0.88717. This is not a test result.

`scripts/train-v4-remaining.ps1` now runs electrical recovery first and parking second, stopping if either command fails. Electrical recovery initializes saved model weights, but starts a new optimizer and epoch counter. It writes to a separate `data/image-v4-electrical-recovery` directory, preserving the original run and its history. Parking uses `data/image-v4-parking-run`.

Training output: `data/training-v4.log`. Errors: `data/training-v4-error.log`. Final metrics are only available after the run creates its `data/image_metrics.json`; an epoch score alone is not completion.

Electrical data: 11,509 retained component crops, with 7,978 training, 1,889 validation and 1,642 test images. Acquisition-date groups are separated. These include augmented views and do not represent 11,509 independent photographs. Classes cover corrosion, intact equipment, missing insulator caps and nests. They do not establish power outages or whether a streetlight works.

Parking data: 6,000 images, with 3,459 training, 1,485 validation and 1,056 test images. Entire scenes are separated between splits. Three views per vehicle mean these are not 6,000 independent vehicles. Within-bay, crossing-bay and outside-bay class names are inferred from visual inspection, not author-confirmed legal categories. The data was photographed in China, not Lucknow.

The website still uses the deployed v3 model. New specialists need evaluation on full photographs and correct scene selection before deployment. Binary sign and electrical crop models must not be applied indiscriminately to all uploads.

Road acceptance evaluation uses thresholds chosen exclusively on validation data. `scripts/evaluate_road_cascade.py --split test` writes full held-out predictions; `scripts/evaluate_road_acceptance.py` then reports accepted predictions, false positives, precision and recall. This is the existing v3 test set, not a new external test.

The optional road-refinement response now identifies both model versions and architectures. Eight image unit tests pass. This metadata change does not activate the candidate on the website.

Road test evaluation completed on 1,651 images. Pothole F1 improved from 0.5960 to 0.6709; road-surface F1 improved from 0.5618 to 0.6656. Garbage F1 remained 0.9516. Using validation-selected thresholds, accepted pothole predictions had 106 correct out of 113 (93.81% precision), but accepted recall was only 41.57%. Surface predictions had 102 correct out of 123 (82.93% precision), below the desired 90%; surface must remain manual review. Do not tune thresholds against these test results and then call the same test independent validation. Results: data/image-v4-road-recovery/data/cascade_selective_test.json.

## Road pipeline deployed and verified

The website now uses **image-v4-road**. This supersedes the earlier status above that v3 alone was deployed. The base v3 model is preserved at `ml/image_model.pt`; the road specialist is `ml/image_road_model.pt`; `ml/image_pipeline.json` selects the combined pipeline. `ml/image_pipeline.py` loads both and tracks timestamps for both models plus configuration. Remove the configuration file to roll back to the preserved base model and base report.

The public `/api/image-metrics` endpoint serves `data/image_pipeline_metrics.json` when the pipeline is configured. `data/image_metrics.json` continues to document the original base model. The webpage shows the combined confusion matrix and per-class test results, while distinguishing the base and road training histories. The road model reuses a subset of the base corpus; the two dataset counts must not be added as unique images.

The combined acceptance policy accepted 175 / 1,651 held-out test photos (10.60% coverage), with 165 / 175 correct (94.29% precision). Only garbage and sufficiently confident pothole matches may suggest a category. Road surface issues remain manual review. Text still determines routing.

Verification: 11 Python image/pipeline tests passed, including comparison of real-photo inference against saved evaluation predictions; 14 API tests passed using a temporary store; production Vite build passed; interface detector reported no findings. Live health reported AI available and Neon PostgreSQL connected. Live metrics endpoint returned image-v4-road. No screenshot-based visual check was performed in this pass.

Electrical recovery remains in progress (two completed recovery epochs at the last check; best validation macro F1 92.57%). Parking remains queued behind it. Sign, electrical and parking defect specialists have NOT been deployed. The full retraining task is therefore not complete.
