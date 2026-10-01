import csv, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from ml.service import Prediction, Duplicate, Candidate, predict, duplicates, haversine
class TriageTests(unittest.TestCase):
 def test_family_isolation(self):
  with Path('data/synthetic_complaints.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
  sets={s:{r['family'] for r in rows if r['split']==s} for s in ['train','validation','test']}
  self.assertFalse(sets['train']&sets['test']);self.assertFalse(sets['train']&sets['validation']);self.assertFalse(sets['validation']&sets['test'])
 def test_jurisdiction(self):
  for text in ['National highway has a pothole','Open drain is blocked near the road','My passport application is delayed']:
   self.assertTrue(predict(Prediction(text=text))['manualReview'])
 def test_external_translation_and_text_isolation(self):
  from ml.train import fingerprint
  with Path('data/training_complaints.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
  groups={};texts={};ids={}
  for r in rows:
   self.assertEqual(groups.setdefault(r['family'],r['split']),r['split'])
   if r['source'].startswith('Civic'):
    self.assertEqual(texts.setdefault(fingerprint(r['text']),r['split']),r['split'])
    original=r['id'].rsplit('-',1)[0]
    self.assertEqual(ids.setdefault(original,r['split']),r['split'])
   elif r['split']!='train':self.fail('Synthetic support leaked into external evaluation')
  self.assertGreater(len(rows),30000)
 def test_multilingual_basic_routing(self):
  cases=[('कचरा सड़क पर पड़ा है और सफाई नहीं हुई','Garbage'),('sadak par gaddha hai road needs repair','Road Damage'),('Streetlight is not working outside our house','Streetlight'),('पानी की सप्लाई बंद है','Water Supply')]
  for text,label in cases:
   with self.subTest(text=text):self.assertEqual(predict(Prediction(text=text))['category'],label)
 def test_uncertain(self):
  self.assertTrue(predict(Prediction(text='xyzzy qwerty blorpt'))['manualReview'])
 def test_safety(self):
  self.assertEqual(predict(Prediction(text='Streetlight pole has an exposed live wire and a person is injured'))['urgency'],'High')
 def test_distance(self):
  self.assertAlmostEqual(haversine(26.85,80.95,26.85,80.95),0)
  self.assertGreater(haversine(26.85,80.95,26.86,80.95),1000)
 def test_duplicate_boundaries(self):
  now=datetime.now(timezone.utc);text='Garbage has not been collected near the market for three days.'
  def candidate(id,lat=26.85,age=1,status='Assigned',category='Garbage',description=text):
   return Candidate(id=id,description=description,lat=lat,lng=80.95,createdAt=(now-timedelta(days=age)).isoformat(),category=category,status=status)
  found=duplicates(Duplicate(text=text,lat=26.85,lng=80.95,category='Garbage',candidates=[candidate('yes'),candidate('far',lat=26.86),candidate('old',age=8),candidate('closed',status='Resolved'),candidate('wrong',category='Streetlight'),candidate('future',age=-1),candidate('different',description='Routine sweeping maintenance requested near a public garden')]))
  self.assertEqual([x['id'] for x in found['matches']],['yes'])
if __name__=='__main__':unittest.main(verbosity=2)
