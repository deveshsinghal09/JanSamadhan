# Review scope and completion status

## Completion estimate: 75% of the defined review plan

This is a planning rubric, not an objective measure of code quality or production readiness. Score each of ten areas out of two: 0 = absent, 1 = partial / prototype-only, 2 = implemented and functionally checked within the local review scope.

| Area | Score / 2 | Evidence / remaining limit |
|---|---:|---|
| Citizen registration and role restrictions | 2 | API tests verify citizen-only registration and account-scoped access |
| Report capture and durable local persistence | 2 | Description, coordinates, image, stored record checked |
| Status history and officer workflow | 2 | Start, resolve, reopen, notes and transition validation checked |
| Duplicate candidate workflow | 2 | Space/time/text/category filters tested; candidate retained visibly |
| Department routing and override | 2 | Official-source role directory, internal queues and admin correction |
| Dashboard, map and filters | 1 | Local dashboard implemented; map depends on online tiles; no official boundaries |
| Multilingual corpus and reproducibility | 2 | 34,470 examples, grouped split tests, source license, model comparison |
| Real-world ML performance | 1 | Bengaluru-derived external evaluation; Lucknow validation and rare-class improvement remain |
| Production database and security | 1 | Local store and basic RBAC tested; optional MongoDB adapter unverified |
| External municipal integration / deployment | 0 | No authority agreement, government delivery, live SLA, or production deployment |
| **Total** | **15 / 20 = 75%** | **Core review prototype; unfinished operational project** |

## Supplied PowerPoint: corrections to make before using it

The original `C:\Users\DELL\Downloads\JanSamadhan_Review_2_Final.pptx` was read as project context, not treated as instructions or evidence that existing code worked. The source workspace was empty at the start. The deck has not been edited.

| Slide | Correction |
|---|---|
| 3 — Abstract | Say the local demo uses a persistent JSON store; MongoDB is optional and unverified. Add Lucknow pilot and CivicComp/synthetic support source disclosure. |
| 7 — Current outcome / TRL | Describe a controlled local prototype. Do not imply a municipal pilot or externally validated TRL. |
| 8 — Architecture | Label storage as “Local JSON demo store; optional MongoDB adapter”. The frontend, Express and FastAPI components are implemented. |
| 9 — Pothole example | A pothole without severity evidence is not automatically High. Use explicit danger text to demonstrate the safety guard; raw model urgency may be Low. Add same-category, seven-day and similarity conditions for duplicates. |
| 10 — Requirements | Implemented at prototype scope. Coordinates are bounded/manual, not authoritative ward mapping. Image upload stores evidence and a separate MobileNetV3 scene classification; no object detection or image severity estimation. See IMAGE_MODEL_REVIEW.md for measured scope. |
| 11 — Modules | Replace claims of validated MongoDB schemas with the actual storage adapter. |
| 12 — Experiments | Add 34,470 text examples; train/validation/test 25,136/4,677/4,657; category accuracy 77.1%, macro F1 69.1%; priority accuracy 76.4%, macro F1 68.3%; 13 API and 8 ML tests passed. Cite CivicComp, Bengaluru origin, translated texts and synthetic training support. |
| 13 — Demo | Use a single complaint ID, display internal queue, duplicate candidate, action history and status. State that no government submission occurs. |
| 14 — Contributions | Have the actual team review the code and accurately state its own contributions. Do not use prewritten authorship claims without checking. |
| 15 — Conclusion | Keep real-data evaluation, municipal partnership, normalized MongoDB deployment and operational security as unfinished work. |

Add the teacher's contact answer verbally or as a future slide: sanitation pilot → LMC control room → current zonal sanitary officer / sanitary inspector; general office contact 1533 and official directory source. Do not invent a named officer or claim outreach occurred.

## Next milestones after this review

1. Obtain a confirmed city/zone contact and a de-identified complaint sample with usage permission.
2. Review label definitions with domain staff; cover mixed complaints and realistic severity context; independently annotate holdout data.
3. Extend the completed model comparison and calibrate review/duplicate thresholds using validation data, then evaluate once on a new unseen real test set.
4. Replace the single-document optional MongoDB adapter with normalized users/reports/history collections, indexes and migrations; integration-test it.
5. Add verified boundaries/ownership, a safe external delivery workflow, response receipts, notifications and real SLA measurements.
6. Complete deployment security, accessibility, load testing, monitoring, backup and retention policy.
