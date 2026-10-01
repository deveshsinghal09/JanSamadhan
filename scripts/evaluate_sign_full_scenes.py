"""Check crop-trained sign predictions on their held-out full source photos.

This is a transfer check, not an independent external benchmark. A full scene may
contain additional signs; disagreement requests review rather than proving error.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import csv,io,json
from pathlib import Path
from PIL import Image,ImageOps
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ml.vision import ImageClassifier
from sklearn.metrics import classification_report,confusion_matrix

def main():
 base=ROOT/'data/images/v4-sources/sign-defects'
 originals={}
 for path in sorted(base.glob('*/images/*.jpg')):originals.setdefault(path.stem.split('.rf.')[0],path)
 with (ROOT/'data/images/v4-sign-prepared/manifest.csv').open(encoding='utf8') as f:rows=[r for r in csv.DictReader(f) if r['split']=='test']
 model=ImageClassifier(ROOT/'data/image-v4-sign-run/ml/image_model.pt')
 results=[]
 for row in rows:
  if row['source_family'].startswith('RF:'):path=originals[row['source_family'][3:]]
  else:path=ROOT/'data/images/v3-sources/sign-scenes'/Path(row['path']).name
  with Image.open(path) as source:
   image=ImageOps.exif_transpose(source).convert('RGB');image.thumbnail((768,768));buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=90)
  predicted=model.predict(buffer.getvalue())
  results.append({'path':path.relative_to(ROOT).as_posix(),'expected_crop_condition':row['label'],'prediction':predicted['label'],'confidence':predicted['confidence'],'group':row['group']})
 truth=[r['expected_crop_condition'] for r in results];pred=[r['prediction'] for r in results]
 report={'modelVersion':model.version,'samples':len(results),'report':classification_report(truth,pred,labels=model.labels,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(truth,pred,labels=model.labels).tolist(),'labels':model.labels,'results':results,
 'limitations':'Full photos corresponding to held-out crops, not an independent external sample. Labels describe selected sign crops and may not describe all signs in a scene. Scores do not establish legality or sign location.'}
 out=ROOT/'data/image-v4-sign-run/data/full_scene_evaluation.json';out.write_text(json.dumps(report,indent=2));print(json.dumps(report['report'],indent=2))

if __name__=='__main__':main()
