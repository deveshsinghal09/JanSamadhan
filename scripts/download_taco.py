"""Download official TACO resized photos for local training; retain provenance.

Photos are not redistributed in the review package. Resume by rerunning.
"""
import concurrent.futures, hashlib, io, json, urllib.request
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/images'
DEST=BASE/'raw/taco'

def main():
 data=json.loads((BASE/'taco_annotations.json').read_text())
 DEST.mkdir(parents=True,exist_ok=True)
 annotated={a['image_id'] for a in data['annotations']}
 images=[im for im in data['images'] if im['id'] in annotated]
 def download(im):
  path=DEST/f"taco_{im['id']:05}.jpg"
  url=im.get('flickr_640_url') or im['flickr_url']
  try:
   if not path.exists():
    request=urllib.request.Request(url,headers={'User-Agent':'JanSamadhan-academic-dataset/2.0'})
    with urllib.request.urlopen(request,timeout=35) as response:raw=response.read(15*1024*1024)
    with Image.open(io.BytesIO(raw)) as photo:
     photo.convert('RGB').save(path,quality=95)
   with Image.open(path) as photo:photo.verify()
   return {'id':im['id'],'path':path.relative_to(ROOT).as_posix(),'url':url,'original_url':im['flickr_url'],'license':im.get('license'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  except Exception as e:return {'id':im['id'],'error':str(e),'url':url}
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for result in pool.map(download,images):
   results.append(result)
   if len(results)%100==0:print('Downloaded',len(results),'/',len(images),'failures',sum('error' in r for r in results),flush=True)
 report={'source':'https://github.com/pedropro/TACO','annotation_sha256':hashlib.sha256((BASE/'taco_annotations.json').read_bytes()).hexdigest(),'policy':'Official annotated images only, 640px URLs. Local research use; metadata has missing per-image licenses, so no photo redistribution. No unlabeled images assigned as garbage.','images':results}
 (BASE/'taco_download.json').write_text(json.dumps(report,indent=2))
 print('DONE',len(results),'failures',sum('error' in r for r in results),flush=True)
if __name__=='__main__':main()
