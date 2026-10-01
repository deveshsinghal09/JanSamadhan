"""Evaluate road refinement across the complete v3 test set, including garbage.
Candidate only: does not alter deployed model files or the website.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from PIL import Image,ImageOps
from sklearn.metrics import classification_report,confusion_matrix
from ml.vision import ImageClassifier

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--split',choices=['test','validation'],default='test');args=parser.parse_args()
 base=ImageClassifier();road=ImageClassifier(ROOT/'data/image-v4-road-recovery/ml/image_model.pt')
 with (ROOT/'data/images/manifest.csv').open(encoding='utf8') as f:rows=[r for r in csv.DictReader(f) if r['split']==args.split]
 indices=[base.labels.index(label) for label in road.labels];truth=[];old=[];new=[];all_scores=[]
 with torch.inference_mode():
  for start in range(0,len(rows),16):
   images=[]
   for row in rows[start:start+16]:
    path=ROOT/'.training-tmp/image-cache'/f"{row['sha256']}.png"
    if not path.exists():path=ROOT/row['path']
    with Image.open(path) as source:im=ImageOps.exif_transpose(source).convert('RGB');im.thumbnail((768,768));images.append(im)
   p=torch.softmax(base.model(torch.stack([base.preprocess(im) for im in images]))/base.temperature,1).numpy()
   q=torch.softmax(road.model(torch.stack([road.preprocess(im) for im in images]))/road.temperature,1).numpy()
   combined=p.copy()
   # Retain the base model's total probability for road scenes and all non-road scores.
   combined[:,indices]=p[:,indices].sum(axis=1,keepdims=True)*q
   truth.extend(base.labels.index(r['label']) for r in rows[start:start+16]);old.extend(p.argmax(1));new.extend(combined.argmax(1))
   all_scores.extend(combined.tolist())
   if start%160==0:print('Cascade evaluation',start,'/',len(rows),flush=True)
 report={'samples':len(rows),'labels':base.labels,'base_report':classification_report(truth,old,target_names=base.labels,output_dict=True,zero_division=0),'cascade_report':classification_report(truth,new,target_names=base.labels,output_dict=True,zero_division=0),'cascade_confusion_matrix':confusion_matrix(truth,new).tolist(),
 'policy':'Road specialist redistributes only the base road probability mass; other class scores remain unchanged. Evaluated on the existing v3 test set, not an independent external test. Acceptance thresholds require validation-set calibration separately.'}
 report['split']=args.split
 if args.split=='validation':
  scores=np.asarray(all_scores);actual=np.asarray(truth);evidence={}
  for label in ('Pothole','Road surface issue'):
   i=base.labels.index(label);chosen_threshold=1.01;accepted=0;precision=None
   for threshold in np.arange(.70,1.,.01):
    mask=(scores.argmax(1)==i)&(scores[:,i]>=threshold)&((np.sort(scores,axis=1)[:,-1]-np.sort(scores,axis=1)[:,-2])>=.15)
    if mask.sum()>=20 and (actual[mask]==i).mean()>=.90:
     chosen_threshold=float(threshold);accepted=int(mask.sum());precision=float((actual[mask]==i).mean());break
   evidence[label]={'threshold':chosen_threshold,'accepted':accepted,'precision':precision}
  report['acceptance_evidence']=evidence
 counts={r['group']:sum(x['group']==r['group'] for x in rows) for r in rows}
 report['group_weighted_report']=classification_report(truth,new,target_names=base.labels,sample_weight=[1/counts[r['group']] for r in rows],output_dict=True,zero_division=0)
 report['predictions']=[{'path':r['path'],'group':r['group'],'truth':int(t),'prediction':int(n),'scores':s} for r,t,n,s in zip(rows,truth,new,all_scores)]
 filename='cascade_evaluation.json' if args.split=='test' else 'cascade_validation.json'
 path=ROOT/'data/image-v4-road-recovery/data'/filename;path.write_text(json.dumps(report,indent=2))
 print(json.dumps({label:{'base_f1':report['base_report'][label]['f1-score'],'cascade_f1':report['cascade_report'][label]['f1-score']} for label in base.labels},indent=2))

if __name__=='__main__':main()
