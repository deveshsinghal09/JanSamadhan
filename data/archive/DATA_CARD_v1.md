# Dataset card — JanSamadhan Lucknow synthetic v1

## What the dataset is

3,888 **synthetic**, authored complaint examples for a controlled student prototype. They are not real Lucknow complaints, not sampled citizens and not official resolution statistics. Approximate Lucknow locality points provide demonstration geography. There are no real names, telephone numbers, addresses or government complaint IDs in the training data.

Generator: `ml/train.py`, random seed **42**. Reproduce with `.venv\Scripts\python.exe -m ml.train` after setting `OPENBLAS_NUM_THREADS=1`.

## Logic that can be explained

Each row combines:

1. A complaint phrase belonging to one of six categories: Garbage, Road Damage, Streetlight, Water Supply, Sewerage, Other.
2. An explicitly authored urgency context: Low = routine inconvenience; Medium = sustained disruption; High = stated immediate risk/injury.
3. One of six approximate locality points: Hazratganj, Gomti Nagar, Aliganj, Alambagh, Indira Nagar, Chowk.
4. Small random latitude/longitude offsets (±0.002 degrees) for simulation only.

No ward or zone boundaries are invented. Severity is independent of category in the generation design: garbage is not automatically Low, and road damage is not automatically High. The text risk context supplies the urgency label. These are project annotation rules, not government SLAs or medical assessments.

The balanced cross-product is intentional for testing. It does not reproduce real complaint frequencies. Some category/risk combinations may be unrealistic; this is a known artifact of the generator and must be improved with human review and real data. Do not use the dataset for municipal resource allocation.

## Split arithmetic

Each category has 12 source phrase families. First assign entire families to splits, then expand:

| Split | Formula | Rows |
|---|---|---:|
| Train | 6 categories × 8 families × 3 urgency labels × 4 urgency phrases × 6 localities | 3,456 |
| Validation | 6 × 2 families × 3 labels × 1 held-out urgency phrase × 6 localities | 216 |
| Test | 6 × 2 families × 3 labels × 1 different held-out urgency phrase × 6 localities | 216 |
| Total | | 3,888 |

Category families and urgency context phrases do not cross splits. The place names are shared by design. This is better than randomly splitting near-identical template expansions, but does not remove shared-author style and vocabulary bias. The benchmark is very small at the distinct-phrase level. Test examples include Hindi/Hinglish families and are deliberately harder than demo examples. No data-driven tuning of the 0.45 routing or 0.72 duplicate thresholds was performed.

## Columns

| Field | Meaning |
|---|---|
| id | Synthetic row ID, SYN-00001 etc. |
| text | Generated complaint + locality + severity context |
| category | Authored six-class label |
| urgency | Authored Low, Medium or High label |
| locality | Named Lucknow reference locality |
| lat, lng | Simulated coordinate near its reference point |
| family | Source category-phrase family identifier |
| split | train, validation or test |
| is_synthetic | True on every row |

The live dashboard is seeded with **24 separate synthetic demonstration records**, not the entire training corpus. Those records have simulated status histories and are visibly labelled. Reports submitted through the UI are user-entered prototype reports; their labels do not imply verified real incidents.

## Model and results

Word TF-IDF unigrams/bigrams with sublinear term frequency; balanced Logistic Regression, max_iter=1200, random_state=42. Only text is passed to the models. Categories, IDs, coordinates, split and urgency columns are not feature inputs. Two classifiers learn category and urgency separately.

Held-out synthetic test macro F1: **category 0.3556; urgency 0.5556**. Full reports and confusion matrices are in model_metrics.json. These modest scores expose the limits of tiny template vocabularies, especially on unseen language forms. They are not real-world accuracy estimates. High scores on familiar demonstration phrases do not contradict poor generalization on held-out phrase families.

The UI also applies conservative jurisdiction and safety guards after raw inference. The benchmark evaluates raw models, not the complete guarded decision policy. Category confidence is an uncalibrated model probability. Vocabulary shown in the UI is a list of recognized terms, not a causal feature attribution. No image model, LLM, speech recognition or translation service is implemented.

## Dataset search and source decision — 8 September 2026

- Kaggle, **Government of India: Grievance report**: https://www.kaggle.com/datasets/ayushyajnik/government-of-india-grievance-report/versions/1 — discovered as a candidate. Row-level Lucknow suitability and usable license were not verified; not downloaded or used.
- Kaggle, **1.2M Complaints BMC Predict Civic Satisfaction**: https://www.kaggle.com/competitions/mumbai-nagar-seva-bmc-civic-complaint-resolution-2018-2024 — discovery result concerns Mumbai, not the chosen UP pilot. Not downloaded or used; underlying provenance not validated.
- Janaagraha IChangeMyCity AWS registry: https://registry.opendata.aws/ichangemycity/ — official registry marks this distribution deprecated and says the provider no longer provides data through that mechanism. Not used.

This was a focused search, not proof that no suitable UP dataset exists. The user explicitly allowed a logical synthetic fallback. No dataset is relabelled as Lucknow data, and no synthetic data is described as Kaggle data.

## Routing reference sources, not training complaint sources

- https://lmc.up.nic.in/helpline.aspx — current official control-room contact, directly retrieved 2026-09-08.
- https://lmc.up.nic.in/pdf/amrut/OfficersinLNN.pdf — historical directory supporting engineering and sanitation role names; current individuals not asserted.
- https://lmc.up.nic.in/pdf/citysanitaionplan.pdf — historical sanitation institutional context; no claim of current operator roster.
- https://jklmc.gov.in/Contact.aspx — official Jal Kal contact directory was found in search; direct request failed with a gateway error. Confirm current zone contacts before external use.

Official role structure informs a **proposed** application mapping; officials did not approve the prototype. Any real deployment needs de-identified complaints, consent/permission as applicable, independent labelling, a time-separated evaluation set, a validated municipal boundary and explicit asset ownership.
