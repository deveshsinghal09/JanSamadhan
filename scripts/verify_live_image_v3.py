"""Read-only photo predictions through the actual web API; no complaint is created."""
import csv,json,urllib.request,http.cookiejar,io,uuid
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:3001/api'
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None,content_type='application/json'):
 req=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':content_type,'Origin':'http://127.0.0.1:3001'})
 return json.load(opener.open(req,timeout=40))
if __name__=='__main__':
 metrics=request('/image-metrics');assert metrics['modelVersion']=='image-v3'
 request('/auth/login',json.dumps({'email':'citizen@demo.in','password':'Review@123'}).encode())
 rows=list(csv.DictReader((ROOT/'data/images/manifest.csv').open(encoding='utf8')));results=[]
 for label in ('Garbage / litter','Waterlogging / flooded road','Traffic sign / review','Other / review'):
  row=next(r for r in rows if r['split']=='test' and r['label']==label)
  with Image.open(ROOT/row['path']) as im:photo=ImageOps.exif_transpose(im).convert('RGB')
  photo.thumbnail((768,768));buffer=io.BytesIO();photo.save(buffer,format='JPEG',quality=95)
  boundary='JanSamadhan'+uuid.uuid4().hex
  body=(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="verification.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode()+buffer.getvalue()+f'\r\n--{boundary}--\r\n'.encode()
  result=request('/predict-image',body,'multipart/form-data; boundary='+boundary)
  assert result['modelVersion']=='image-v3'
  assert len(result['scores'])==8
  record={'expected':label,'predicted':result['label'],'confidence':result['confidence'],'manualReview':result['manualReview'],'modelVersion':result['modelVersion'],'source_path':row['path']}
  results.append(record);print(json.dumps(record),flush=True)
 (ROOT/'data/images/v3-live-verification.json').write_text(json.dumps(results,indent=2))
 request('/auth/logout',b'{}')
