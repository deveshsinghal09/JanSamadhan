import math, re, base64, binascii, threading
from datetime import datetime, timezone
from pathlib import Path
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity

app=FastAPI(title='JanSamadhan triage',version='0.8.0')
models=joblib.load(Path(__file__).with_name('models.joblib'))
image_classifier=None
image_signature=None
image_lock=threading.Lock()
class ImagePrediction(BaseModel):
 imageBase64:str=Field(min_length=20,max_length=4194304)

@app.post('/predict-image')
def predict_image(body:ImagePrediction):
 global image_classifier,image_signature
 try:
  raw=base64.b64decode(body.imageBase64,validate=True)
  with image_lock:
   from ml.image_pipeline import signature,load_classifier
   current_signature=signature()
   if image_classifier is None or current_signature!=image_signature:
    image_classifier=load_classifier()
    image_signature=current_signature
   return image_classifier.predict(raw)
 except (ValueError,binascii.Error) as e:raise HTTPException(status_code=400,detail=str(e))
 except (FileNotFoundError,ImportError) as e:raise HTTPException(status_code=503,detail='Image model not installed; run image training/setup') from e
class Prediction(BaseModel):
 text:str=Field(min_length=10,max_length=3000)
class Candidate(BaseModel):
 id:str
 description:str
 lat:float
 lng:float
 createdAt:str
 category:str
 status:str
class Duplicate(Prediction):
 lat:float
 lng:float
 category:str
 candidates:list[Candidate]=Field(default_factory=list,max_length=5000)

def haversine(a,b,c,d):
 p,q=math.radians(c-a),math.radians(d-b)
 h=math.sin(p/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(q/2)**2
 return 6371000*2*math.asin(min(1,math.sqrt(h)))

@app.get('/health')
def health():return {'status':'ok','model':'CivicComp multilingual TF-IDF + Logistic Regression','data':'Bengaluru-derived corpus + Lucknow synthetic training support','version':'2.0','imageModelAvailable':Path(__file__).with_name('image_model.pt').exists(),'imageModelLoaded':image_classifier is not None}
@app.post('/predict')
def predict(body:Prediction):
 result={}
 for target,model in models.items():
  probabilities=model.predict_proba([body.text])[0]; index=int(probabilities.argmax())
  result[target]=str(model.classes_[index]);result[target+'Confidence']=round(float(probabilities[index]),4)
  if target=='category':result['scores']={str(c):round(float(p),4) for c,p in zip(model.classes_,probabilities)}
 model_category=result['category'];raw_urgency=result['urgency']
 result['modelCategory']=model_category;result['modelUrgency']=raw_urgency
 # Conservative explicit guards complement the learned model.
 outside=re.search(r'\b(nhai|national highway|pwd|lda|passport|police|pension|ration|household electricity|power outage|private apartment)\b',body.text,re.I)
 open_drain=re.search(r'\b(open drain|roadside drain|nala|naali)\b|नाली',body.text,re.I)
 low=result['categoryConfidence']<.45
 result['manualReview']=bool(low or outside or open_drain or model_category=='Other')
 result['reason']='Ownership / out-of-scope review required' if outside or open_drain else 'Low confidence; officer must classify' if low else 'Predicted from complaint text'
 if result['manualReview']:result['category']='Other'
 # Word-boundary safety cues, negation-aware for common English phrases. Still requires human review.
 danger=re.search(r'(?<!no )(?<!not )\b(electrocution|injured|injury|live wire|ambulance.*blocked|children sick|immediate danger)\b|तुरंत खतरा|घायल',body.text,re.I)
 result['safetyOverride']=bool(danger)
 if danger:result['urgency']='High'
 vectorizer=models['category'].named_steps['tfidf']
 if hasattr(vectorizer,'transformer_list'):vectorizer=dict(vectorizer.transformer_list)['word']
 vector=vectorizer.transform([body.text])
 terms=vectorizer.get_feature_names_out()
 result['matchedTerms']=[str(terms[i]) for i in vector.indices[:12]]
 result['method']='CivicComp-trained multilingual TF-IDF + Logistic Regression; jurisdiction and safety guards; model v2'
 return result

@app.post('/duplicates')
def duplicates(body:Duplicate):
 matches=[]; now=datetime.now(timezone.utc);vectorizer=models['category'].named_steps['tfidf']
 if hasattr(vectorizer,'transformer_list'):vectorizer=dict(vectorizer.transformer_list)['word']
 for c in body.candidates:
  age=(now-datetime.fromisoformat(c.createdAt.replace('Z','+00:00'))).total_seconds()/86400
  if c.status=='Resolved' or c.category!=body.category or not 0<=age<=7:continue
  distance=haversine(body.lat,body.lng,c.lat,c.lng)
  if distance>150:continue
  vectors=vectorizer.transform([body.text,c.description]);score=float(cosine_similarity(vectors[0],vectors[1])[0][0])
  if score>=.72:matches.append({'id':c.id,'similarity':round(score,3),'distanceMeters':round(distance,1),'ageDays':round(age,2)})
 return {'matches':sorted(matches,key=lambda x:-x['similarity']),'criteria':{'minSimilarity':.72,'maxDistanceMeters':150,'maxAgeDays':7},'note':'Candidates only. Citizen may keep a distinct report; reports are never silently discarded.'}
