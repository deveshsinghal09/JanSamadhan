# CivicComp-HiEn: Multilingual Civic Complaint Dataset

![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)
![Kaggle](https://img.shields.io/badge/Platform-Kaggle-blue)
![Dataset](https://img.shields.io/badge/Type-Multilingual%20Dataset-green)

---

## 📋 Dataset Overview

**CivicComp-HiEn** is a multilingual civic complaint dataset containing aligned complaints in **English**, **Hindi**, and **Hinglish** (Hindi–English code-mixed text). The dataset is derived from real-world civic complaints submitted to the Bruhat Bengaluru Mahanagara Palike (BBMP), Bengaluru, India, and has been carefully processed to preserve privacy while enabling multilingual NLP research.

Each complaint is available as a **parallel triplet** across the three languages, sharing a common identifier.

---

## 🎯 Intended Use

This dataset is designed for:

* Multilingual and cross-lingual NLP research
* Machine translation (EN–HI, EN–Hinglish, HI–Hinglish)
* Civic complaint and grievance classification
* Code-mixed language understanding
* Urban governance and civic-tech applications
* Educational and academic research purposes

---

## 📁 Files in This Dataset

| File Name     | Description                  | Records | Format   |
| ------------- | ---------------------------- | ------- | -------- |
| `train.csv`   | Training split               | 8,000   | CSV      |
| `dev.csv`     | Development/validation split | 1,600   | CSV      |
| `test.csv`    | Test split                   | 1,600   | CSV      |
| `LICENSE.txt` | License information          | —       | Text     |
| `README.md`   | Dataset documentation        | —       | Markdown |

---

## 📊 Dataset Schema

All dataset splits share the same schema:

| Column Name          | Description                 | Example                                 |
| -------------------- | --------------------------- | --------------------------------------- |
| `id`                 | Unique complaint identifier | `BBMP_0000001`                          |
| `complaint_en`       | Complaint text in English   | “Garbage not collected for 3 days”      |
| `complaint_hi`       | Complaint text in Hindi     | “कचरा 3 दिन से नहीं उठाया गया है”       |
| `complaint_hinglish` | Complaint text in Hinglish  | “Garbage 3 din se nahi uthaya gaya hai” |
| `category`           | Complaint category          | `Sanitation`                            |
| `split`              | Dataset split               | `train` / `dev` / `test`                |

---

## 🔧 Data Processing

### Preprocessing Steps

1. **Privacy Preservation**
   All personally identifiable information (PII), including phone numbers, email addresses, and exact addresses, was removed using rule-based anonymization.

2. **Identifier Standardization**
   Each complaint was assigned a new standardized identifier in the format:
   `BBMP_XXXXXXXX` (e.g., `BBMP_0000001`).

3. **Multilingual Expansion**
   For every English complaint, aligned **Hindi** and **Hinglish** versions were created and annotated using the same identifier to ensure strict cross-lingual alignment.

4. **Quality Control**
   Translations were verified to preserve semantic meaning and natural linguistic usage, particularly for Hinglish code-mixed text.

5. **Dataset Splitting**
   The dataset was split into **train**, **development**, and **test** sets with fixed sizes to support reproducible benchmarking.

---

## 📈 Dataset Statistics

| Split     | English    | Hindi      | Hinglish   |
| --------- | ---------- | ---------- | ---------- |
| Train     | 8,000      | 8,000      | 8,000      |
| Dev       | 1,600      | 1,600      | 1,600      |
| Test      | 1,600      | 1,600      | 1,600      |
| **Total** | **11,200** | **11,200** | **11,200** |

* **Aligned triplets:** 16,000
* **Total text instances:** 48,000 (EN + HI + Hinglish)

---

## 📜 Citation

If you use this dataset, please cite:

```bibtex
@INPROCEEDINGS{11489415,
  author={Tripathi, Shyam and Hridayesh, Kothamasu and Ashwini, K.},
  booktitle={2026 International Conference on Wireless Communications Signal Processing and Networking (WiSPNET)}, 
  title={CivicComp: A Hindi–English Corpus for Automated Civic Complaint Categorization}, 
  year={2026},
  volume={},
  number={},
  pages={1-6},
  keywords={Wireless communication;Communication systems;Computer networks;Protocols;HTTP;Internet;Regional area networks;Electronic mail;Radio access networks;Storage area networks;Civic Grievance;Multilingual Text Classification;Low-Resource NLP;Dataset Benchmarking;Hindi-English Code-Mixing},
  doi={10.1109/WiSPNET69615.2026.11489415}}
```
