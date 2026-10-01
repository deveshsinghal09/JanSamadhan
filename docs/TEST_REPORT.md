# Latest verification — 9 September 2026

- 15 Python tests and 14 API integration tests passed (29 total). API tests use an isolated temporary local store with dotenv disabled; they do not modify Neon.
- Browser checks verified visible validation feedback, routing preview, submission and immediate report display.
- A 4.27 MB outdoor-litter photo was resized in the browser and saved successfully (604,453 bytes).
- Live Neon verification confirmed the new report and photo were readable after restarting the API. The image returned by the API matched the database bytes by SHA-256.
- The temporary verification report was then removed by exact ID, owner and description; its photo was removed by the foreign-key cascade.
- Final state: 1 preexisting submitted report preserved, 0 seeded reports, 8 review users, 0 photos. Health check: API OK, AI available, database available, storage Neon PostgreSQL.
- The production frontend build passed. Image-v2 is active.

The older record below describes earlier builds; seeded duplicate testing has been replaced by a genuine test submission followed by duplicate preview. Sessions are intentionally reset on API restart.

---

# Verification record — 8 September 2026

## Automated checks

**13 / 13 API integration tests passed against the live v2 AI service** using a separate server on port 3012 and a temporary database. These verify:

- Unauthenticated requests are denied.
- Demo authentication succeeds and wrong credentials fail.
- Registration cannot grant itself administrator access; a new citizen sees no other citizen's reports.
- Garbage prediction and seeded duplicate candidate work together.
- Outside-pilot coordinates are rejected.
- PNG image, report and duplicate acknowledgement persist; authorized image retrieval works.
- An officer's list is department-scoped; cross-department modification and image access fail.
- Citizens cannot change status; officers cannot skip directly from Assigned to Resolved.
- Officer updates and administrator reopening produce history entries.
- Priority corrections enforce role/department scope, validate the label, persist audit history and preserve raw model evidence.
- National-highway ownership uncertainty routes to review; administrator can record a correction.
- A script disguised as a PNG is rejected.
- Cross-origin writes fail; logout invalidates the session.

**8 / 8 ML tests passed:** category family isolation across splits, known jurisdiction guards, unknown-text review, safety cue escalation, Haversine distance, duplicate exclusions for distant/old/resolved/different-category/future/dissimilar records, source-ID/translation/normalized-text split isolation and basic English/Hindi/Hinglish routing.

**Frontend production build passed** after final UI changes (Vite 6.4.3). Build output: approximately 390 kB JavaScript and 61 kB CSS, before compression. These are build sizes, not a performance benchmark.

The first API run encountered transient memory-allocation errors. The final sequential run passed all 13 tests. Training was run with OPENBLAS_NUM_THREADS=1. This is documented in the launch/setup scripts. No security audit, load benchmark or MongoDB integration test was performed.

## Browser verification

The Codex in-app browser was used to:

- Inspect the citizen dashboard visually at a desktop viewport.
- Submit the garbage sample through the actual form.
- Verify Garbage → LMC Sanitation / Health → Zonal Sanitary Officer / Sanitary Inspector.
- See duplicate JS-DEMO-001 at 0 metres / 100% text similarity for the identical sample.
- Acknowledge the candidate and save new complaint **JS-5EE9527C60**.
- Switch to sanitation officer, start work with an action note, and mark the report resolved with a second note.
- Switch back to citizen and verify the same ID is Resolved.
- Reload the rebuilt frontend and confirm the stored case remains visible.
- Inspect the map's account-scoped point markers and category totals. The base tiles were not visible in the observed screenshot; successful external tile delivery is not claimed.
- Inspect the Model & dataset page and its 34,470-example total, grouped split counts, candidate comparison, language results and per-class results. Switch to priority and expand the confusion matrix.

This browser test added one clearly simulated user-entered report to the classroom database, alongside the 24 seeded records. Its action notes explicitly identify browser verification. Nothing was sent to a government service.

A stale success notice between account switches and retained page scroll on navigation were corrected. The frontend was rebuilt and citizen sign-in was rechecked afterward. The hero and report form were separately checked at 390 px in the earlier UI pass. The new evidence page was checked at the current narrow in-app viewport. Geolocation permission and physical-device accuracy were not tested. Image upload was checked through the HTTP integration test rather than the browser file picker.

## Launch verification

`scripts/start.ps1 -NoBrowser` successfully restarted both localhost services and passed health checks. START_DEMO.cmd calls the same script and opens the default browser. Setup dependencies are installed, model and CSV generated, and frontend build present in this workspace. For another computer, run SETUP.cmd; no cross-machine installation test was performed.

## UI refresh

Refined the interface with a deep-green sidebar, amber accents, larger typography, clearer status labels, and more consistent cards, forms and report details. The production frontend build passes. Browser visual checks covered the desktop dashboard at 1366 px and the report form at 390 px. That earlier UI pass changed presentation only. The subsequent v2 update below changes model training and adds priority correction.

## Lucknow photograph hero

Added a locally bundled Rumi Darwaza photograph to the dashboard hero and sign-in page, with responsive crops, dark overlays, editorial typography and working report/track navigation. Dribbble references and the photo's source, attribution and CC BY-SA 4.0 license are documented in IMAGE_CREDITS.md. The final production build passed. Browser screenshots checked the desktop hero, 390 px mobile hero and desktop sign-in page. The photograph is bundled at 1280 × 854 pixels (337 kB) for offline use.

## Multilingual model v2 verification

Training completed on this machine using 25,136 training texts. Validation chose word+character features for both models. The 4,657-text external test produced category accuracy 0.7709 / macro F1 0.6909 and priority accuracy 0.7640 / macro F1 0.6833. Full values and class supports are in data/model_metrics.json. Source/license/audit details are in data/DATA_CARD.md.

The old live servers were detected holding v1 in memory; only the identified project processes were restarted. AI health now reports version 2.0 and the live dataset endpoint downloads training_complaints.csv. API tests were rerun successfully against this service; their setup now explicitly rejects a stale AI version.

Browser verification as sanitation officer changed seeded report JS-DEMO-016 from Medium to High using the new priority selector. Its status stayed Assigned, and the visible history includes the exact reason prefixed with “Browser verification only”. This is a simulated action on an existing synthetic case.

Final browser check: Hindi text 'कचरा सड़क पर पड़ा है और सफाई नहीं हुई' analyzed through the live citizen form as Garbage, Assigned, LMC Sanitation / Health, with the Zonal Sanitary Officer / Sanitary Inspector role. This is a functional smoke check, not an independent benchmark. No additional report was submitted.


## Image model update — 9 September 2026

13 Python tests (8 text/routing + 5 image/split/metric checks) and 14 HTTP integration tests passed: **27 total**. Production build passed (~398 kB JS, 61 kB CSS). Image tests cover invalid/tiny/oversized input, score contract, source-family/hash isolation, near-hash isolation and manifest/metric consistency. Integration tests verify login-required photo analysis, valid seven-class response, saved photo prediction and account-scoped evidence access. A discovered 422-to-503 invalid-file mapping was corrected and the integration suite rerun successfully.

The final model was trained on 7,564 images and selected using 1,639 validation images; held-out test has 1,611 images. Accuracy 93.6%, macro F1 85.1%. Epoch 2 won; the deployed CNN backbone is frozen and its classifier head is trained. CNN fine-tuning was evaluated but not selected. Dataset/license/limitations and source checksums are documented separately.

Final browser smoke check: signed in as the demo citizen, attached data/images/demo/pothole-test.jpg through the file picker and clicked Classify attached photo. The live UI returned Pothole (displayed model score 100.0%) and Road Damage, with the advisory/unsupported-scene warning visible. This is a single functional check, not an additional accuracy benchmark. No complaint was submitted during this check.

Department contact fix: replaced vague Source actions with expandable View contacts panels. Verified LMC contact details against its official helpline page on 9 September 2026. Jal Kal direct page failed retrieval; water/sewer panels explicitly offer an LMC referral, not a direct Jal Kal officer contact. Historical PDFs remain separately labelled background references. Production build passed; browser verified the expanded Water Supply panel and contact link targets. No calls or emails were sent.
