import base64,csv,io,json,unittest
from pathlib import Path
from PIL import Image
from ml.vision import ImageClassifier,decode_image

class ImageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.classifier=ImageClassifier()
 def test_invalid_and_tiny_images_rejected(self):
  for raw in [b'not a photo',b'x'*(3*1024*1024+1)]:
   with self.assertRaises(ValueError):decode_image(raw)
  buffer=io.BytesIO();Image.new('RGB',(1,1)).save(buffer,format='PNG')
  with self.assertRaises(ValueError):decode_image(buffer.getvalue())
 def test_road_refinement_preserves_nonroad_probability_and_total(self):
  import numpy as np
  class RoadStub:
   labels=['Pothole','Road scene / review','Road surface issue']
   def scores_for_image(self,image):return np.array([.2,.3,.5])
  classifier=self.classifier;image=Image.new('RGB',(224,224),(50,70,90))
  original=classifier.road_refiner
  try:
   classifier.road_refiner=None;before=classifier.scores_for_image(image)
   classifier.road_refiner=RoadStub();after=classifier.scores_for_image(image)
   indices=[classifier.labels.index(label) for label in RoadStub.labels]
   self.assertAlmostEqual(float(after.sum()),1.,places=5)
   self.assertTrue(np.allclose(after[indices],before[indices].sum()*np.array([.2,.3,.5])))
   for i,label in enumerate(classifier.labels):
    if label not in RoadStub.labels:self.assertEqual(before[i],after[i])
  finally:classifier.road_refiner=original
 def test_model_output_contract(self):
  buffer=io.BytesIO();Image.new('RGB',(224,224),(50,70,90)).save(buffer,format='PNG')
  result=self.classifier.predict(buffer.getvalue())
  self.assertIn(result['label'],self.classifier.labels)
  self.assertAlmostEqual(sum(result['scores'].values()),1,places=3)
  metrics=json.loads(Path('data/image_metrics.json').read_text())
  self.assertEqual(result['modelVersion'],metrics['modelVersion'])
  self.assertIn('Unsupported scenes',result['note'])
  if result['manualReview']:
   self.assertIsNone(result['suggestedCategory'])
   self.assertEqual(result['displayLabel'],'Photo needs review')
  self.assertGreater(self.classifier.temperature,0)
 def test_split_families_pixels_and_hashes_do_not_cross(self):
  with Path('data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
  for key in ['group','source_family','pixel_hash','sha256','dhash']:
   assigned={}
   for row in rows:self.assertEqual(assigned.setdefault(row[key],row['split']),row['split'])
  self.assertGreater(len(rows),1000)
 def test_no_near_hash_leakage(self):
  from ml.train_images import HashTree
  with Path('data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
  tree=HashTree()
  for i,row in enumerate(rows):
   for j in tree.neighbors(int(row['dhash'])):self.assertEqual(row['split'],rows[j]['split'])
   tree.insert(int(row['dhash']),i)
 def test_outdoor_litter_is_batch_isolated_and_present_in_each_split(self):
  with Path('data/images/manifest.csv').open(encoding='utf8') as f:rows=[r for r in csv.DictReader(f) if '/taco/' in r['path']]
  metrics=json.loads(Path('data/image_metrics.json').read_text())
  self.assertGreater(len(rows),50 if metrics['modelVersion']=='image-v3' else 500)
  assigned={}
  for row in rows:self.assertEqual(assigned.setdefault(row['source_family'],row['split']),row['split'])
  self.assertEqual({r['split'] for r in rows},{'train','validation','test'})
  if metrics['modelVersion']=='image-v3':
   annotations=json.loads(Path('data/images/taco_annotations.json').read_text())
   counts={}
   for a in annotations['annotations']:counts[a['image_id']]=counts.get(a['image_id'],0)+1
   for row in rows:self.assertGreaterEqual(counts[int(Path(row['path']).stem.split('_')[-1])],5)
 def test_review_only_classes_cannot_route_even_at_high_score(self):
  import torch
  original=self.classifier.model
  class Fixed(torch.nn.Module):
   def __init__(self,index,n):super().__init__();self.index=index;self.n=n
   def forward(self,x):
    logits=torch.full((len(x),self.n),-20.);logits[:,self.index]=20.;return logits
  buffer=io.BytesIO();Image.new('RGB',(224,224),(50,70,90)).save(buffer,format='PNG')
  try:
   for label in [l for l in self.classifier.labels if l not in ('Garbage / litter','Pothole')]:
    self.classifier.model=Fixed(self.classifier.labels.index(label),len(self.classifier.labels))
    result=self.classifier.predict(buffer.getvalue())
    self.assertTrue(result['manualReview']);self.assertIsNone(result['suggestedCategory'])
  finally:self.classifier.model=original
 def test_metrics_match_manifest(self):
  with Path('data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
  m=json.loads(Path('data/image_metrics.json').read_text())
  self.assertEqual(m['audit']['retained_images'],len(rows))
  self.assertEqual(m['test']['report']['macro avg']['support'],sum(r['split']=='test' for r in rows))
  self.assertEqual(m['best_epoch'],max(m['history'],key=lambda e:e['validation_macro_f1'])['epoch'])
  import hashlib
  self.assertEqual(m['model_sha256'],hashlib.sha256(Path('ml/image_model.pt').read_bytes()).hexdigest())
  self.assertEqual(m['manifest_sha256'],hashlib.sha256(Path('data/images/manifest.csv').read_bytes()).hexdigest())
  if m['modelVersion']=='image-v3':
   self.assertNotIn('Damaged road sign',self.classifier.labels)
   self.assertIn('Waterlogging / flooded road',self.classifier.labels)
   self.assertFalse(any('dataset-resized' in r['path'] or '/raw/data/' in r['path'] for r in rows))
if __name__=='__main__':unittest.main()
