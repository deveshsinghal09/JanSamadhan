# ML review: the facts to present

The project now trains two multilingual text classifiers locally. It compares word-only TF-IDF against word + character TF-IDF, both with balanced Logistic Regression. The latter wins on validation for both category and priority. For these text classifiers, no pretrained third-party weights were used; they were fitted on this computer. The separate image model uses official ImageNet initialization followed by local civic-image training; see IMAGE_MODEL_REVIEW.md.

| Stage | Text examples | Purpose |
|---|---:|---|
| Training | 25,136 | Fit vocabulary, IDF and classifier weights |
| Validation | 4,677 | Choose between candidate feature representations |
| Test | 4,657 | Report held-out results after selection |
| Total | 34,470 | Not a count of independent citizens |

Data consists of 31,014 cleaned external text examples and 3,456 authored training examples. All validation and test examples are external. Hindi and Hinglish are aligned translations of the underlying English source complaints.

| Target | Validation word F1 | Validation word+char F1 | Test accuracy | Test macro F1 |
|---|---:|---:|---:|---:|
| Category | 65.0% | 67.5% | 77.1% | 69.1% |
| Priority | 61.9% | 67.2% | 76.4% | 68.3% |

Macro F1 averages the class F1 scores equally; accuracy measures the fraction of correct text predictions. The rare Sewerage class has only 15 test texts and 26.7% F1. The result is too uncertain for autonomous sewer/drain routing. Priority is learned from supplied severity annotations, which include keyword-derived scores; it is not verified emergency assessment.

## Explain the architecture

1. A citizen types English, Hindi or Hinglish text.
2. Word unigrams/bigrams and character 3–5-grams convert text into sparse TF-IDF features. Each vocabulary is fitted only on training text.
3. Separate balanced Logistic Regression models predict category and priority. Only complaint text is used; label columns, severity scores, locations and status are not model features.
4. Explicit rules flag jurisdiction ambiguity and danger cues. A department-role directory maps accepted categories to Lucknow queues.
5. Duplicate candidates combine word cosine similarity, same category, time and distance. Citizen acknowledgement preserves the new report.
6. Officers can correct priority; administrators can correct department. Both require an explanation, preserve the original prediction and add history.

## Explain the data and split

Source: [CivicComp-HiEn on Kaggle](https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints), CC BY-SA 4.0. Publisher reports Bengaluru/BBMP origins, not Lucknow. The actual downloaded CSVs contain 8,000 + 1,600 + 1,600 records. We recombine and regroup them; we do not claim to reproduce the publisher's benchmark.

Source identifiers and normalized matching text form connected groups. Translation siblings and identical normalized text cannot cross splits. Groups with conflicting mapped category or priority labels are removed (619 records). Groups are stratified by category into 70/15/15 using seed 42. Exact duplicates are removed globally. Semantic paraphrases may still cross groups; no temporal holdout or independent Lucknow evaluation has been performed.

Our model learns issue language from the external corpus. Our separate Lucknow directory proposes responsible roles. This is a domain-transfer prototype; training on Bengaluru does not establish Lucknow effectiveness.

## Show it live

Open Model & dataset. Show the source, training count, comparison, per-class results, language breakdown and confusion matrix. Then submit a garbage report, acknowledge a repeat candidate, sign in as sanitation officer, correct priority with a reason, start work and resolve. Sign in as citizen to show the same ID and history.

Reproduce training in PowerShell:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
npm run train
```

The recorded run took about 60 seconds on this machine; time varies. It writes `data/training_complaints.csv`, `data/model_metrics.json`, and `ml/models.joblib`. Restart the AI service after retraining; an already-running process keeps its loaded model. Source CSVs and licenses are bundled, so training needs no Kaggle login after setup.

Do not present the previous 35.6% synthetic category F1 versus the new 69.1% as a controlled improvement: the benchmark changed. The word-only versus word+character validation comparison above uses the same data and split and is a fair comparison.

Attribution: Original creators Vivek Mathew and Haji Shariefullah via OpenCity; CivicComp enhancements by Shyam Tripathi, Kothamsu Hridayesh, K. Ashwini and Kritika Agrahari, Amrita Vishwa Vidyapeetham, Chennai Campus. Derived data is distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See the full source license in `data/external/civiccomp/License.txt`.
