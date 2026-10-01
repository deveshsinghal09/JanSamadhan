"""Reproducible grouped multilingual training: python -m ml.train."""
import csv,json,re,hashlib,time
from collections import Counter,defaultdict
from pathlib import Path
import joblib,numpy as np
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.model_selection import train_test_split
from ml.synthetic import generate
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://www.kaggle.com/datasets/shyamtripathi373/civiccomp-hien-hindienglish-civic-complaints'
MAPPING={'Garbage Dumping & Black Spots':'Garbage','Garbage Collection':'Garbage','Street Cleanliness':'Garbage','Animal & Organic Waste':'Garbage','Waste Segregation & Processing':'Garbage','Construction & Debris Waste':'Garbage','Road Damage & Potholes':'Road Damage','Streetlights & Public Lighting':'Streetlight','Water Supply Issues':'Water Supply','Water Leakage & Wastage':'Water Supply','Water Pipeline & Infrastructure':'Water Supply','Water Quality & Metering':'Water Supply','Drainage & Sewage':'Sewerage'}
def clean(text):
 text=re.sub(r'https?://\S+|www\.\S+',' URL ',text)
 text=re.sub(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}',' EMAIL ',text)
 text=re.sub(r'(?<!\d)(?:\+91[ -]?)?[6-9](?:[ -]?\d){9}(?!\d)',' PHONE ',text)
 return ' '.join(text.split())
def fingerprint(text):return ' '.join(re.sub(r'[^\w\s]','',re.sub(r'\d+',' NUM ',text.lower())).split())
def prepare():
 records=[]
 for split in ['train','dev','test']:
  with (ROOT/f'data/external/civiccomp/{split}.csv').open(encoding='utf-8-sig') as f:records.extend(csv.DictReader(f))
 parent=list(range(len(records)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 seen={}
 for i,r in enumerate(records):
  for key in [r['original_id']]+[fingerprint(clean(r[c])) for c in ['text_en','Hindi','Hinglish'] if r[c].strip()]:
   if key in seen:parent[find(i)]=find(seen[key])
   else:seen[key]=i
 groups=defaultdict(list)
 for i,r in enumerate(records):groups[find(i)].append(r)
 valid=[];conflicts=0
 for group in groups.values():
  if len({(MAPPING.get(r['category_secondary'],'Other'),r['severity']) for r in group})>1:conflicts+=len(group);continue
  valid.append(group)
 ids=list(range(len(valid)));strata=[MAPPING.get(g[0]['category_secondary'],'Other') for g in valid]
 train_ids,hold=train_test_split(ids,test_size=.30,stratify=strata,random_state=42)
 val_ids,test_ids=train_test_split(hold,test_size=.5,stratify=[strata[i] for i in hold],random_state=42)
 assignment={i:s for s,subset in [('train',train_ids),('validation',val_ids),('test',test_ids)] for i in subset}
 rows=[];used=set()
 for i,group in enumerate(valid):
  gid='CIVIC-'+hashlib.sha256(min(r['original_id'] for r in group).encode()).hexdigest()[:12]
  for r in group:
   for lang,col in [('English','text_en'),('Hindi','Hindi'),('Hinglish','Hinglish')]:
    text=clean(r[col]);key=fingerprint(text)
    if len(text)<10 or key in used:continue
    used.add(key)
    rows.append(dict(id=f'{r["original_id"]}-{lang}',text=text,category=MAPPING.get(r['category_secondary'],'Other'),urgency=r['severity'].title(),language=lang,family=gid,split=assignment[i],source='CivicComp / Bengaluru',is_synthetic=False))
 for r in generate():
  if r['split']=='train':rows.append({k:r[k] for k in ['id','text','category','urgency','family','split','is_synthetic']}|{'language':'Mixed authored','source':'Lucknow synthetic support'})
 with (ROOT/'data/training_complaints.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
 return rows,{'downloaded_records':len(records),'downloaded_text_slots':len(records)*3,'conflicting_records_removed':conflicts,'source_groups_after_conflict_removal':len(valid),'external_texts_after_cleaning':sum(r['source'].startswith('Civic') for r in rows),'synthetic_training_texts':sum(r['is_synthetic'] for r in rows),'split_policy':'70/15/15 stratified by category at connected source-ID/normalized-text group level; all translations stay together. Conflicting groups excluded. Exact normalized text deduplicated globally. Near paraphrases can remain.'}
def report(model,rows,target):
 y=[r[target] for r in rows];p=model.predict([r['text'] for r in rows])
 return {'report':classification_report(y,p,output_dict=True,zero_division=0),'labels':model.classes_.tolist(),'confusion_matrix':confusion_matrix(y,p,labels=model.classes_).tolist()}
def make_model(kind):
 word=TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=45000,sublinear_tf=True,dtype=np.float32)
 features=word if kind=='word' else FeatureUnion([('word',word),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=3,max_features=55000,sublinear_tf=True,dtype=np.float32))])
 return Pipeline([('tfidf',features),('classifier',LogisticRegression(C=4,max_iter=450,class_weight='balanced',random_state=42,tol=.001))])
def main():
 started=time.time();rows,audit=prepare();train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation'];test=[r for r in rows if r['split']=='test']
 models={};result={'comparisons':{}}
 for target in ['category','urgency']:
  candidates={};comparison={}
  for kind in ['word','word_char']:
   print('Training',target,kind,len(train),'texts',flush=True);m=make_model(kind)
   m.fit([r['text'] for r in train],[r[target] for r in train]);candidates[kind]=m
   comparison[kind]=report(m,val,target)['report']['macro avg']['f1-score'];print('Validation macro F1',comparison[kind],flush=True)
  winner=max(comparison,key=comparison.get);model=candidates[winner];models[target]=model
  result['comparisons'][target]={'validation_macro_f1':comparison,'selected':winner}
  result[target]={'validation':report(model,val,target),'test':report(model,test,target),'by_language':{lang:report(model,[r for r in test if r['language']==lang],target) for lang in ['English','Hindi','Hinglish']}}
  print(target,'test macro F1',result[target]['test']['report']['macro avg']['f1-score'],flush=True)
 joblib.dump(models,ROOT/'ml/models.joblib',compress=3)
 result.update(seed=42,rows=len(rows),splits=dict(Counter(r['split'] for r in rows)),audit=audit,source=SOURCE,license='CC BY-SA 4.0',method='Balanced Logistic Regression; word TF-IDF versus word + character TF-IDF selected independently for each target using validation macro F1. Text is the only model input.',limitations='External benchmark is Bengaluru-derived with translated Hindi/Hinglish, not measured Lucknow performance. Severity labels are supplied keyword-based annotations, not verified emergencies. Drainage & Sewage is a broad proxy; open drains require manual ownership review. Exact duplicate groups are isolated; semantic near-duplicates may remain. Synthetic support is training-only. Scores are uncalibrated probabilities; officers must review ambiguous cases.',threshold=.45,training_seconds=round(time.time()-started,1),class_counts={s:{t:dict(Counter(r[t] for r in rows if r['split']==s)) for t in ['category','urgency']} for s in ['train','validation','test']},dataset_sha256=hashlib.sha256((ROOT/'data/training_complaints.csv').read_bytes()).hexdigest())
 (ROOT/'data/model_metrics.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print(json.dumps({'rows':len(rows),'splits':result['splits'],'seconds':result['training_seconds']},indent=2),flush=True)
if __name__=='__main__':main()
