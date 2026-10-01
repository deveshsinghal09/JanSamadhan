"""Compare semantic and supervised road gating using validation only for selection."""
import csv,json
from pathlib import Path
import joblib,numpy as np
from scipy.special import softmax,log_softmax
from sklearn.metrics import classification_report,f1_score
root=Path(__file__).resolve().parents[1];out=root/'data/image-v6-clip-run'
with (root/'data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
a=joblib.load(out/'classifier.joblib');labels=a['labels'];x=np.load(out/'features.npz')['features'];z=100*x@a['text_features'].T
linear=a['model'].decision_function(x);q=np.load(out/'road_probabilities.npy');indices=[labels.index(l) for l in ['Pothole','Road scene / review','Road surface issue']]
y=np.array([labels.index(r['label']) for r in rows]);v=np.array([r['split']=='validation' for r in rows]);t=np.array([r['split']=='test' for r in rows]);trials=[];best=None
for alpha in [0,.25,.5,.75,1]:
 p=softmax((1-alpha)*log_softmax(linear,axis=1)+alpha*log_softmax(z,axis=1),axis=1)
 for road_weight in [0,.25,.5,.75,1]:
  combined=p.copy();combined[:,indices]=(1-road_weight)*p[:,indices]+road_weight*p[:,indices].sum(1,keepdims=True)*q
  score=f1_score(y[v],combined[v].argmax(1),average='macro')
  trial={'semantic_weight':alpha,'road_weight':road_weight,'validation_macro_f1':score};trials.append(trial)
  if best is None or score>best[0]:best=(score,trial,combined)
score,chosen,p=best
report={'selected':chosen,'trials':trials,'test':classification_report(y[t],p[t].argmax(1),target_names=labels,output_dict=True,zero_division=0),'policy':'Validation-only selection. Existing repeatedly evaluated test split; no new benchmark. No deployment.'}
for alpha in [0,.25,.5,.75,1]:
 p0=softmax((1-alpha)*log_softmax(linear,axis=1)+alpha*log_softmax(z,axis=1),axis=1)
 report.setdefault('validation_by_class',{})[str(alpha)]=classification_report(y[v],p0[v].argmax(1),target_names=labels,output_dict=True,zero_division=0)
(out/'gating_comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps({'selected':chosen,'test_macro_f1':report['test']['macro avg']['f1-score'],'validation_semantic_only':report['validation_by_class']['1']['macro avg']['f1-score']},indent=2))
