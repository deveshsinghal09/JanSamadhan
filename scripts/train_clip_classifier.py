"""Fit a civic classifier on frozen CLIP features; select hyperparameters on validation only."""
import csv,json,sys,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report,confusion_matrix,log_loss,f1_score
from scipy.special import softmax,log_softmax
from scipy.optimize import minimize_scalar
from ml.clip_features import PROMPTS
out=ROOT/'data/image-v6-clip-run';started=time.time()
with (ROOT/'data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
assert hashlib.sha256((ROOT/'tests/fixtures/external-pothole.jpg').read_bytes()).hexdigest() not in {r['sha256'] for r in rows}
labels=sorted(PROMPTS);cache=np.load(out/'features.npz');assert int(cache['done'])==len(rows)
x=cache['features'];y=np.array([labels.index(r['label']) for r in rows]);splits={s:np.array([r['split']==s for r in rows]) for s in ('train','validation','test')}
z=100*x@np.load(out/'text_features.npy').T;best=None;trials=[]
for c in (.1,1.,10.,100.):
 model=LogisticRegression(C=c,class_weight='balanced',max_iter=2000,random_state=42).fit(x[splits['train']],y[splits['train']])
 linear=model.decision_function(x)
 for alpha in (0.,.25,.5,.75,1.):
  logits=(1-alpha)*log_softmax(linear,axis=1)+alpha*log_softmax(z,axis=1)
  score=f1_score(y[splits['validation']],logits[splits['validation']].argmax(1),average='macro')
  trials.append({'C':c,'semantic_weight':alpha,'validation_macro_f1':float(score)})
  if best is None or score>best[0]:best=(score,model,c,alpha,logits)
score,model,c,alpha,logits=best;v=splits['validation'];t=splits['test']
objective=lambda temperature:log_loss(y[v],softmax(logits[v]/temperature,axis=1),labels=list(range(len(labels))))
temp=float(minimize_scalar(objective,bounds=(.1,10.),method='bounded').x)
prob=softmax(logits/temp,axis=1);thresholds={};evidence={}
for i,label in enumerate(labels):
 threshold=1.01;ev={'accepted':0,'precision':None}
 if label in ('Pothole','Garbage / litter'):
  for candidate in np.arange(.70,1.,.01):
   p=prob[v];mask=(p.argmax(1)==i)&(p[:,i]>=candidate)&((np.sort(p,axis=1)[:,-1]-np.sort(p,axis=1)[:,-2])>=.15)
   if mask.sum()>=20 and (y[v][mask]==i).mean()>=.9:threshold=float(candidate);ev={'accepted':int(mask.sum()),'precision':float((y[v][mask]==i).mean())};break
 thresholds[label]=threshold;evidence[label]=ev
artifact={'model':model,'labels':labels,'semantic_weight':alpha,'text_features':np.load(out/'text_features.npy'),'temperature':temp,'class_thresholds':thresholds,'version':'image-v6-clip-candidate','prompts':PROMPTS}
joblib.dump(artifact,out/'classifier.joblib')
counts={r['group']:sum(a['group']==r['group'] and a['split']=='test' for a in rows) for r in rows if r['split']=='test'}
report={'version':artifact['version'],'architecture':'Frozen CLIP ViT-B/32 + supervised Logistic Regression and validation-selected semantic blending','selected':{'C':c,'semantic_weight':alpha,'temperature':temp},'trials':trials,'validation':classification_report(y[v],prob[v].argmax(1),target_names=labels,output_dict=True,zero_division=0),'test':classification_report(y[t],prob[t].argmax(1),target_names=labels,output_dict=True,zero_division=0),'group_test':classification_report(y[t],prob[t].argmax(1),target_names=labels,sample_weight=[1/counts[r['group']] for r in rows if r['split']=='test'],output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(y[t],prob[t].argmax(1)).tolist(),'class_thresholds':thresholds,'validation_threshold_evidence':evidence,'splits':{s:int(m.sum()) for s,m in splits.items()},'labels':labels,'manifest_sha256':hashlib.sha256((ROOT/'data/images/manifest.csv').read_bytes()).hexdigest(),'checkpoint_sha256':hashlib.sha256((out/'classifier.joblib').read_bytes()).hexdigest(),'fit_seconds':time.time()-started}
p=prob[t];accepted=np.array([p[i].max()>=thresholds[labels[int(p[i].argmax())]] and np.sort(p[i])[-1]-np.sort(p[i])[-2]>=.15 for i in range(len(p))]);report['selective_test']={'accepted':int(accepted.sum()),'coverage':float(accepted.mean()),'precision':float((p[accepted].argmax(1)==y[t][accepted]).mean()) if accepted.any() else None}
report['predictions']=[{'path':r['path'],'truth':int(a),'prediction':int(b.argmax()),'scores':b.tolist()} for r,a,b in zip([r for r in rows if r['split']=='test'],y[t],prob[t])]
(out/'metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps({'selected':report['selected'],'test':report['test'],'selective_test':report['selective_test']},indent=2),flush=True)
