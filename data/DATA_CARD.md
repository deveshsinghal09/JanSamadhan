# Dataset card — JanSamadhan multilingual v2

## Source and license

Primary training source: CivicComp-HiEn version 3 on Kaggle, downloaded 8 September 2026.
https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints

The publisher describes complaints derived from Bengaluru/BBMP records with Hindi and Hinglish translations. This is NOT a Lucknow dataset. The application separately focuses its proposed department routing and demo geography on Lucknow, Uttar Pradesh.

Attribution: This work is based on data originally created by Vivek Mathew and Haji Shariefullah (via Opencity.in), with modifications and enhancements by the CivicComp-HiEn research team (Shyam Tripathi, Kothamsu Hridayesh, K. Ashwini, Kritika Agrahari) from Amrita Vishwa Vidyapeetham, Chennai Campus. Licensed under Creative Commons Attribution-ShareAlike 4.0 International.

The downloaded source files and publisher documentation are retained under data/external/civiccomp. Derived training_complaints.csv is also distributed under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/. Modifications: text field selection; basic phone/email/URL masking; normalization, conflict removal and deduplication; new group splits; category mapping; synthetic training support. Publisher licenses are preserved unchanged. The downloaded CSVs have additional address columns despite the publisher's anonymization statement; our derived file omits those columns. Text can still contain personal names or landmarks: the simple masking is not a certified anonymization process.

Publisher README contains inconsistent totals and a simplified schema. Actual file counts and columns were inspected: train.csv 8,000; dev.csv 1,600; test.csv 1,600. We use original_id, text_en, Hindi, Hinglish, category_secondary and severity. We recombine and split independently; our results are not the publisher's benchmark.

## Actual counts

- Downloaded: 11,200 source rows, 33,600 translated text slots.
- Removed: 619 source rows in normalized duplicate groups with contradictory mapped category/priority labels.
- Remaining source groups: 10,202; some groups contain multiple source records.
- Retained external text examples after blank/short filtering and global normalized deduplication: 31,014.
- Additional authored Lucknow training examples: 3,456.
- Combined: 34,470 text examples. Train 25,136; validation 4,677; test 4,657.

Translations are not independent complaints. We do not inflate the number of citizens by counting translated texts. Dataset SHA-256 and per-class split counts are in model_metrics.json.

## Label mapping

| External secondary label | Application category |
|---|---|
| Garbage Dumping & Black Spots; Garbage Collection; Street Cleanliness; Animal & Organic Waste; Waste Segregation & Processing; Construction & Debris Waste | Garbage |
| Road Damage & Potholes | Road Damage |
| Streetlights & Public Lighting | Streetlight |
| Water Supply Issues; Water Leakage & Wastage; Water Pipeline & Infrastructure; Water Quality & Metering | Water Supply |
| Drainage & Sewage | Sewerage (broad proxy; open drains need manual ownership review) |
| All remaining secondary labels | Other / internal review |

Priority uses the supplied LOW/MEDIUM/HIGH annotation, converted to title case. Source columns include severity_score and high/medium keyword matches; these suggest a rule-based annotation policy, not independent municipal urgency decisions. Those columns are NEVER inputs to the model. Some source labels are vague or inconsistent; we have not manually relabelled the entire corpus.

## Leakage controls

Before splitting, union records sharing an original ID or any normalized English/Hindi/Hinglish text. Normalization lowercases, removes punctuation, collapses spaces and replaces numeric runs. Remove contradictory-label groups. Stratify groups by application category into 70/15/15 with seed 42. All translations stay together. Deduplicate normalized text globally. Fit vocabulary, IDF and classifier only on train. Select between word-only and word+character models using validation macro F1. Test never selects the model. Automated checks assert translation-ID, family and normalized-text isolation.

Semantic near-duplicates and recurring writing patterns can remain. This is a grouped random split, not a temporal holdout. No claim of complete leakage elimination, independent translations, calibrated reliability or city-transfer performance is made.

## Synthetic support

ml/synthetic.py retains the original deterministic generator: six categories, 12 phrase families per category, three urgency contexts and six approximate Lucknow localities. Only its 3,456 training rows enter v2. Its 216 validation and 216 test rows do not enter v2 evaluation. The original complete 3,888-row synthetic CSV remains available for reproducibility. Synthetic combinations can be unnatural and are not prevalence estimates. They support rare category vocabulary; they do not substitute for real labelled examples.

## Model results

Two balanced Logistic Regression classifiers, C=4, max_iter=450, tol=0.001, seed 42. Word TF-IDF: 1–2 grams, min_df=2, max 45,000 features. Character TF-IDF: char_wb 3–5 grams, min_df=3, max 55,000 features. Sublinear term frequency. Both candidates are fitted on identical train data; both targets select word+character features on validation.

| Target | Word validation macro F1 | Word+char validation macro F1 | Test accuracy | Test macro F1 |
|---|---:|---:|---:|---:|
| Category | 0.6495 | 0.6749 | 0.7709 | 0.6909 |
| Priority | 0.6187 | 0.6725 | 0.7640 | 0.6833 |

Sewerage test F1 is 0.2667 on only 15 texts; this is a substantial limitation. Full confusion matrices, precision, recall and language results are in model_metrics.json and the website. Raw models are evaluated before jurisdiction/safety guards. Scores are not calibrated probabilities of correctness. This corpus cannot establish real Lucknow performance. The original synthetic benchmark is archived under data/archive and is not directly comparable.

## Reproduction and use

Run npm run train with OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. All CSV sources are bundled; no API credentials or third-party model weights are used. Training writes the derived CSV, metrics JSON and joblib models. Download training_complaints.csv from the evidence page.

The live dashboard contains submitted prototype reports, not the training corpus. The earlier 24 demonstration seeds were removed and automatic complaint seeding is disabled. No imported Bengaluru complaint is placed into a Lucknow operational queue. No government submission takes place.

Other candidates researched but NOT used: abhisheksingh016/citizen-grievance-dataset (CC0; publisher says synthetic, around 3,000 rows); the prior v1 data card lists earlier search results. Research metadata does not imply inclusion in training.

Routing sources are separate from complaint training data: https://lmc.up.nic.in/helpline.aspx, historical role directory https://lmc.up.nic.in/pdf/amrut/OfficersinLNN.pdf, and Jal Kal https://jklmc.gov.in/Contact.aspx (direct retrieval previously failed). Roles are proposed contacts; no current named officer or municipal partnership is asserted.

## Separate image modality

This card describes text training only. The new image classifier has a separate source, split, weights and metrics. See docs/IMAGE_MODEL_REVIEW.md and data/image_metrics.json. Do not combine text and image counts into a single complaint count.
