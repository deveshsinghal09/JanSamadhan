> Image-model correction: see [IMAGE_V2_FIX.md](IMAGE_V2_FIX.md) for the roadside-garbage coverage fix and current limitations. Older image-v1 results below are historical; current metrics are in data/image_metrics.json.

# Panel guide — read this before the review

## Your opening explanation (about 45 seconds)

“JanSamadhan is an AI-assisted civic reporting prototype focused on Lucknow in Uttar Pradesh. A citizen enters a complaint and location. The system suggests a category and urgency, checks for nearby recent duplicates, and routes the report to an internal department queue. An officer records progress and the citizen can track the history. We trained on a licensed multilingual Kaggle corpus derived from Bengaluru complaints, supplemented with authored Lucknow examples. The language model and Lucknow department routing are separate. We have not yet validated it on a Lucknow citizen corpus. This review demonstrates integration and functional correctness, not a government deployment or proven real-world prediction accuracy.”

## Teacher's question: which municipal department, and whom will you contact?

Start with **one concrete primary partner: Lucknow Nagar Nigam's sanitation/health function**. For a pilot about uncollected garbage, request coordination with the **Zonal Sanitary Officer or Sanitary Inspector**, through the **LMC control room**. For institutional permission and escalation, ask the control room to direct the request to the relevant Zonal Officer / Municipal Commissioner's grievance office. This is a proposed engagement route; no office has agreed to work with the project.

Say:

“Sir/Ma'am, we have narrowed the pilot to Lucknow. For garbage collection complaints, our proposed operational contact is the zonal sanitation officer or sanitary inspector of Lucknow Nagar Nigam. We would first contact the official control room on 1533 or nnlko@nic.in to confirm the current officer for the selected locality. Our application routes to a department role, rather than hardcoding a person's name, because postings change. At present those are simulated officer accounts; we have not contacted or integrated with the municipality.”

**Hindi/Hinglish practice:**

“Hum Uttar Pradesh mein Lucknow ko pilot city rakh rahe hain. Kachra na uthne ki complaint ko Nagar Nigam ke sanitation/health desk par route karenge. Iske liye concerned zone ke sanitary officer ya sanitary inspector se coordination propose karte hain. Current officer ka naam aur zone confirm karne ke liye official control room 1533 se contact karenge. Abhi project ke andar demo routing hai; actual municipal integration nahi hui hai.”

Official contact evidence: https://lmc.up.nic.in/helpline.aspx (retrieved 8 September 2026). The page lists 1533, calling/WhatsApp numbers 9219902911–9219902914, email nnlko@nic.in, and the Trilokinath Road, Lalbagh address. These are general office contacts, not a promise that an individual officer will accept a research request.

## The other routes

| Complaint | Proposed responsible desk | Whom to ask for | Important condition |
|---|---|---|---|
| Uncollected garbage | LMC Sanitation / Health | Zonal Sanitary Officer / Sanitary Inspector | Confirm zone and collection responsibility |
| Municipal pothole | LMC Engineering | Junior Engineer, then Executive Engineer for the zone | Verify road ownership; PWD/NHAI/LDA roads must not be blindly routed to LMC |
| Public streetlight | LMC street-lighting desk | Responsible lighting engineer through the control room | Household electricity supply is a different jurisdiction |
| Water supply leak | Jal Kal Water Supply | Executive Engineer for the relevant Jal Kal zone | Verify asset and current zone contact |
| Sewer blockage | Jal Kal Sewerage / designated operator | Zonal engineering desk | Open surface drains may need LMC sanitation or engineering instead |
| Uncertain / outside scope | Internal manual triage | Prototype admin, then confirm competent agency | No automatic guess at an external agency |

The older LMC officer directory supports sanitation/engineering role names. It does **not** verify current names or personal numbers. The Jal Kal contact page was indexed in search, but direct retrieval failed, so do not quote a current named official from it. Source links and limitations are visible inside the app.

## Five-minute demonstration

Because the faculty prioritizes ML, start with **Model & dataset**: source, 25,136 training texts, validation comparison, held-out scores and confusion matrix. Explain one weak category. Then demonstrate the workflow below.

1. **Citizen login:** use citizen@demo.in / Review@123. Explain that seeded reports were removed; only submitted reports are shown.
2. **Report:** choose Report an issue, then Use a garbage collection example. Keep Hazratganj and its default coordinates for a reliable repeat demonstration. Optionally attach a PNG/JPEG photo under 3 MB.
3. **Analyze:** show Garbage → LMC Sanitation / Health → Zonal Sanitary Officer / Sanitary Inspector. Read the confidence as a model score, not guaranteed correctness. The exact demo wording resembles training vocabulary; do not call it an independent benchmark.
4. **Duplicate:** submit one report first, then preview a similar nearby report to show a candidate, distance and text similarity. Acknowledge the link or leave unchecked to keep a distinct case. The system retains the new record either way.
5. **Save:** click Submit report. Note the new complaint ID. Read its history. Explain that no government message was sent.
6. **Officer:** sign out, log in as sanitation@demo.in, open the new complaint. Enter an action note such as “Demo inspection completed; collection team assigned.” You can also select Review priority and record a correction with a reason; the original model prediction stays visible. Click Start work. Enter “Demo collection completed and site checked.” Mark resolved. Do not describe these simulated actions as real municipal work.
7. **Citizen tracking:** sign back in as the citizen; locate the same ID and show Resolved plus history.
8. **Admin (if time):** log in as admin@demo.in. Show department directory, city map and Model & dataset. Explain the ownership-review safeguard with “National highway has a large pothole requiring repairs.” This must go to Needs Review rather than automatically to LMC roads.

If the AI service is unavailable, rerun START_DEMO.cmd. Do not improvise a fake prediction. If map tiles fail without Internet, the local reports, coordinates and analytics still work.

## Questions you should be ready to answer

**Why Lucknow rather than all Uttar Pradesh?**

UP gives a consistent state context, but municipal ownership and officer structures vary by city. Lucknow is a bounded pilot. Supporting all of UP would require city-specific directories, jurisdictions and data. We do not claim current state-wide coverage.

**Where did your data come from?**

CivicComp-HiEn on Kaggle, licensed CC BY-SA 4.0. Its publisher describes English complaints derived from Bengaluru/BBMP records, with Hindi and Hinglish translations. Downloaded files contain 11,200 records (33,600 text slots). After cleaning and conflict filtering, we retained 31,014 external text examples and added 3,456 synthetic training examples: 34,470 total. Do not call these 34,470 independent citizens or Lucknow records. The publisher README has inconsistent totals; our counts come from the actual CSVs. See data/DATA_CARD.md for attribution.

**How is synthetic data logical?**

Each row combines an issue phrase, an urgency context and a locality. Categories represent municipal service problems; severity follows explicit inconvenience, disruption or danger cues. The generator is balanced so the classifier does not simply learn the majority class. This balance is experimental, not a claim about real complaint frequencies. The cross-product can produce unrealistic combinations, so real-data collection and human validation remain necessary.

**How did you prevent leakage?**

We join source IDs and matching normalized texts into groups before a stratified 70/15/15 split. All translations stay in one group. Conflicting label groups (619 records) are excluded; exact normalized duplicates are removed. Final splits: 25,136 training, 4,677 validation and 4,657 test texts. Synthetic support is training-only. Near paraphrases may remain; this is not a time-separated or independently annotated Lucknow evaluation.

**What is TF-IDF? What is Logistic Regression?**

TF-IDF assigns weights to informative words and phrases. Our stronger candidate also learns character fragments of length 3–5, which can help with spelling variants and word forms within each script. This is not translation: Hindi and Hinglish each need training examples. Balanced Logistic Regression learns feature weights for six categories and three urgency labels. We train word-only and word-plus-character candidates for each target, and choose on validation macro F1. Both selected models use word and character features. The test split does not choose the model.

**What are your results?**

Category test accuracy is **77.1%**, macro F1 **69.1%**. Priority accuracy is **76.4%**, macro F1 **68.3%**. These scores use 4,657 held-out external text examples and raw classifiers before safety/routing rules. Validation macro F1 improved from 65.0% to 67.5% for category and 61.9% to 67.2% for priority by adding character features. Sewerage is weak: F1 26.7%, only 15 text examples (translations of a few complaints). Streetlight F1 is 88.1%. Present per-class results, not only accuracy. Severity labels are supplied annotations with keyword scores, not independently verified urgency. We do not claim 90% accuracy or proven Lucknow performance. The old synthetic-only results are archived and are not directly comparable to this different benchmark.

**Why do you call it AI if you also use rules?**

The trained classifiers predict labels from text. Explicit rules separately prevent known out-of-scope routing and raise urgency for certain danger cues. This is a hybrid system. The rule guards are not model predictions and are documented separately.

**Why a 150-metre radius, seven days, and 0.72 similarity?**

They are configurable prototype assumptions. Text alone can merge unrelated places; distance alone can merge different problems. Combining similarity, category, space and time reduces those mistakes. These thresholds still need real-data tuning. “Possible duplicate” is a candidate flag, not proof.

**Does it actually contact a department?**

No. It assigns an internal demo queue and displays the proposed responsible role. We have not sent email, WhatsApp or API calls to government offices. Integration requires authorization, a confirmed interface and a pilot arrangement.

**Where is MongoDB?**

The running application uses Neon PostgreSQL for users, reports, history and photos. Browser submission and persistence after API restart were verified. Without DATABASE_URL it falls back to local JSON. MongoDB is not the current adapter.

**What about security and privacy?**

Passwords are hashed; server-side checks enforce account scope. Photos are access-controlled and limited to 3 MB with PNG/JPEG signatures. Demo accounts are intentionally public. Production deployment still needs persistent sessions, account verification, password recovery, upload sanitization, comprehensive rate limits, retention and backups. Citizens should avoid personal information in photos and descriptions. Do not claim a security audit.

**How will you obtain real data later?**

Request a small de-identified pilot corpus from the confirmed municipal contact, with permission to use complaint text, category, locality and timestamps. Ask multiple domain reviewers to label cases, measure agreement, deduplicate before splitting and hold out a later period. Use observed errors to improve the model and calibrate thresholds. Do not claim this collection has already happened.

**What does 75% complete mean?**

It is a documented planning estimate for the review scope, not a measured software-quality percentage. The core local workflow is implemented and tested. The remaining work is real-world validation, normalized database deployment, municipal integration and operational hardening. See REVIEW_STATUS.md for the rubric.

## Before presenting

Run the demo once yourself and practise the officer/citizen account switch. Know the file names `ml/train.py`, `ml/service.py`, `backend/server.js`, `backend/store.js`, `frontend/main.jsx`, and `data/directory.json`. Do not claim individual team authorship that does not match actual work. The original presentation is unchanged; review its claims using REVIEW_STATUS.md.

## Image-model questions

A separate MobileNetV3-Small CNN now classifies uploaded photos. Read IMAGE_MODEL_REVIEW.md for architecture, seven visual labels, 12,189 retained images, grouped splits and provenance. Training uses 8,495 images, validation 1,906 and test 1,788. The image model does not classify every text category or infer urgency. Show the image section in Model & dataset for actual measured results, and show saved image/text agreement in a report. The raw external archive has weak labels and licensing ambiguity; those limits are documented and raw images are excluded from the review ZIP.
