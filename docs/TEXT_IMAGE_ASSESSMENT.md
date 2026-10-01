# Text + photo assessment — 12 September 2026

Preview now accepts a multipart photograph and description together. Submission re-analyzes both on the server and calls the same `combineEvidence` function in `backend/evidence.js`. Client-supplied model results are never trusted. Text-only JSON preview remains supported.

This is decision-level fusion, not a newly trained multimodal neural network. Both original scores are retained; there is no invented combined confidence. Accepted matching image evidence confirms text. A confident contradictory garbage/road prediction, or a flooding prediction against Road Damage text, retains the text category but requires review. Uncertain or unsupported image evidence cannot overrule text. Existing jurisdiction review and safety priority are preserved.

For example, Road Damage text + 94% Waterlogging / flooded road photo prediction results in Road Damage with Needs Review, with both original predictions visible. It does not claim that the image classifier itself has been corrected. The user's reported photograph was not supplied for direct evaluation in this turn. No held-out pothole in the existing evaluated test set was predicted as flooding, so this failure needs a separate real-world challenge example.

The report form now emphasizes one combined assessment, separates raw photo-only evidence, invalidates preview on photo changes, and disables fields during analysis/submission. Application styles improve type size, form controls, table readability, spacing and mobile layout while retaining Lucknow photography.

Validation: 20 Node tests passed, including fusion disagreements, jurisdiction preservation, and equality of preview/submission evidence with an uploaded image. Production build passed. The interface detector returned no findings. Browser checks at 1440px and 390px verified a real text preview, and both screenshot layouts were visually inspected without horizontal overflow. Test complaints were stored only in a temporary test store. Live API health confirmed AI and Neon connectivity after restart.

Electrical training continues separately; its latest completed recovery epoch was 4 with validation macro F1 94.11%. This is not a final test score. Parking remains queued. These candidate models have not been deployed.

## Exact user-photo regression

The supplied Newport_Whitepit_Lane_pot_hole.JPG was evaluated without adding it to training. The deployed photo classifier incorrectly predicts waterlogging (0.8442). The road specialist alone gives pothole 0.3745, road surface issue 0.4311, and road scene 0.1944; therefore the initial scene error is not the only weakness. The deployed cascade preserves the base road probability mass, so it cannot recover a road scene that the base classifier overwhelmingly calls flooding.

Live multipart preview with this exact photo and a clear pothole description produced Road Damage (text score 0.9995), Needs Review, and a visible text/photo conflict. The example coordinates were preview inputs only; they do not establish that this photograph was taken in Lucknow. No complaint was submitted. Results are saved in data/external-pothole-evaluation.json.

The image is retained only as tests/fixtures/external-pothole.jpg for external regression. It is absent from training manifests. A new API regression checks the combined result and preservation of the raw photo label. All 21 Node tests pass. The photo-only classifier remains wrong on this example; improved combined routing must not be described as corrected image recognition.
