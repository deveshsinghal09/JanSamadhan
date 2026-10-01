"""Deployment tests compare real inference against saved held-out predictions."""
import base64,hashlib,io,json,unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
from ml.image_pipeline import load_classifier,signature
from ml.service import app
ROOT=Path(__file__).resolve().parents[1]
class PipelineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.model=load_classifier()
  cls.metrics=json.loads((ROOT/'data/image_pipeline_metrics.json').read_text())
 def test_artifacts_and_version_match(self):
  self.assertEqual(self.model.version,self.metrics['modelVersion'])
  self.assertEqual(hashlib.sha256((ROOT/'ml/image_road_model.pt').read_bytes()).hexdigest(),self.metrics['pipeline']['road_model_sha256'])
  self.assertEqual(len(signature()),3)
 def test_real_upload_matches_held_out_evaluation(self):
  evaluation=json.loads((ROOT/'data/image-v4-road-recovery/data/cascade_evaluation.json').read_text())
  for label in ('Garbage / litter','Pothole','Road surface issue'):
   index=evaluation['labels'].index(label)
   row=next(r for r in evaluation['predictions'] if r['prediction']==index)
   with Image.open(ROOT/row['path']) as im:
    buffer=io.BytesIO();im.convert('RGB').save(buffer,format='PNG')
   result=self.model.predict(buffer.getvalue())
   self.assertEqual(result['label'],label)
   self.assertAlmostEqual(result['confidence'],max(row['scores']),places=3)
   if label=='Road surface issue':self.assertTrue(result['manualReview'])
 def test_service_uses_pipeline_and_rejects_bad_upload(self):
  client=TestClient(app)
  buffer=io.BytesIO();Image.new('RGB',(224,224)).save(buffer,format='PNG')
  response=client.post('/predict-image',json={'imageBase64':base64.b64encode(buffer.getvalue()).decode()})
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['modelVersion'],self.metrics['modelVersion'])
  response=client.post('/predict-image',json={'imageBase64':'!'*24})
  self.assertEqual(response.status_code,400)
if __name__=='__main__':unittest.main()
