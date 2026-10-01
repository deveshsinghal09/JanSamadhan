"""Candidate checks, including the user's excluded external pothole photograph."""
import csv,hashlib,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from ml.clip_classifier import ClipClassifier
ROOT=Path(__file__).resolve().parents[1]
class ClipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=ROOT/'data/image-v6-clip-run'
  if not (cls.folder/'classifier.joblib').exists():
   raise unittest.SkipTest('Rejected CLIP experiment artifacts are not distributed with the application')
  cls.model=ClipClassifier(cls.folder/'classifier.joblib')
  cls.metrics=json.loads((cls.folder/'metrics.json').read_text())
 def test_external_photo_is_excluded_from_training(self):
  sha=hashlib.sha256((ROOT/'tests/fixtures/external-pothole.jpg').read_bytes()).hexdigest()
  with (ROOT/'data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
  self.assertFalse(any(r['sha256']==sha for r in rows))
 def test_external_pothole_candidate_cannot_auto_route_when_wrong(self):
  result=self.model.predict((ROOT/'tests/fixtures/external-pothole.jpg').read_bytes())
  self.assertAlmostEqual(sum(result['scores'].values()),1,places=3)
  # This rejected experiment confuses the supplied photo with waterlogging.
  # The safety contract is that such a result stays advisory and cannot route
  # the report without complaint text and officer review.
  self.assertTrue(result['manualReview'])
  self.assertIsNone(result['suggestedCategory'])
 def test_live_preprocessing_matches_test_evaluation(self):
  for label in ('Pothole','Garbage / litter','Waterlogging / flooded road'):
   i=self.metrics['labels'].index(label)
   row=next(r for r in self.metrics['predictions'] if r['truth']==i)
   with Image.open(ROOT/row['path']) as im:from PIL import ImageOps;im=ImageOps.exif_transpose(im).convert('RGB');scores=self.model.scores_for_image(im)
   self.assertTrue(np.allclose(scores,row['scores'],atol=.001),label)
 def test_report_matches_saved_classifier(self):
  self.assertEqual(hashlib.sha256((self.folder/'classifier.joblib').read_bytes()).hexdigest(),self.metrics['checkpoint_sha256'])
  self.assertEqual(self.metrics['splits']['test'],len(self.metrics['predictions']))
if __name__=='__main__':unittest.main()
