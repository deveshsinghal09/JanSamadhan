"""Resumable public dataset download; keeps original files and source manifests."""
import concurrent.futures,json,urllib.request,urllib.parse,zipfile,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'data/images/v3-sources'
BASE.mkdir(parents=True,exist_ok=True)
def download(url,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():return
 temp=path.with_suffix(path.suffix+'.part')
 for attempt in range(5):
  offset=temp.stat().st_size if temp.exists() else 0
  try:
   req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
   with urllib.request.urlopen(req,timeout=60) as response:
    mode='ab' if offset and response.status==206 else 'wb'
    with temp.open(mode) as f:
     while True:
      block=response.read(256*1024)
      if not block:break
      f.write(block)
   temp.replace(path);return
  except Exception:
   if attempt==4:raise
   print('retry',path.name,attempt+1,flush=True);time.sleep(2)
def streetlights():
 tree=json.loads((BASE/'streetlights.json').read_text())['tree']
 images=[x for x in tree if x['path'].startswith('Raw Dataset/') and Path(x['path']).suffix.lower() in ('.jpg','.jpeg','.png')]
 def one(x):
  p=x['path'];url='https://raw.githubusercontent.com/Team16Project/Street-Light-Dataset/main/'+urllib.parse.quote(p)
  try:download(url,BASE/'streetlights'/p);return {'path':p,'url':url,'git_blob':x['sha']}
  except Exception as e:return {'path':p,'error':str(e)}
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for r in pool.map(one,images):
   results.append(r)
   if len(results)%100==0:print('streetlights',len(results),'/',len(images),flush=True)
 (BASE/'streetlights-download.json').write_text(json.dumps(results,indent=2));print('streetlights complete',len(results),flush=True)
def flooding():
 url='https://www.kaggle.com/api/v1/datasets/download/saurabhshahane/roadway-flooding-image-dataset'
 dest=BASE/'roadway-flood.zip';download(url,dest)
 with zipfile.ZipFile(dest) as z:
  out=BASE/'roadway-flood'
  for name in z.namelist():
   if not (out/name).resolve().is_relative_to(out.resolve()):raise ValueError('unsafe archive')
  z.extractall(out)
 print('roadway flood complete',len(z.namelist()),flush=True)
def mendeley():
 for name,url in [('civic-page','https://data.mendeley.com/datasets/zndzygc3p3/2'),('civic-api','https://data.mendeley.com/api/datasets/zndzygc3p3/versions/2')]:
  try:download(url,BASE/(name+'.txt'));print(name,'saved',flush=True)
  except Exception as e:print(name,str(e),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(f) for f in [streetlights,flooding,mendeley]]
  for f in futures:
   try:f.result()
   except Exception as e:print(type(e).__name__,str(e),flush=True)
