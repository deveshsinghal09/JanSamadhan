"""Download a reproducible sample of the public sign-type corpus.

Its labels are shape/type, NOT damage. These photos can only teach sign-scene
recognition and must never be used as positive damage annotations.
"""
import concurrent.futures,json,urllib.parse,random,sys
from download_civic_v3 import BASE,download
def one(i):
 extension='txt' if '--annotations' in sys.argv else 'jpg'
 folder='labels' if extension=='txt' else 'dataset'
 name=f'damaged_signs_dataset/{folder}/img_{i}.{extension}'
 url='https://www.kaggle.com/api/v1/datasets/download/danielvareta/damaged-signs-dataset/'+urllib.parse.quote(name,safe='')
 try:
  download(url,BASE/'sign-scenes'/f'img_{i}.{extension}');return {'path':f'img_{i}.{extension}','url':url,'label':'Traffic sign / review'}
 except Exception as e:return {'path':f'img_{i}.{extension}','error':str(e)}
if __name__=='__main__':
 # Metadata inventory confirms the img_N naming scheme, but nonexistent IDs
 # are recorded as failures rather than filled with substitute images.
 ids=list(range(1,501));random.Random(42).shuffle(ids);results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for r in pool.map(one,ids):
   results.append(r)
   if len(results)%50==0:print('Sign photos',len(results),'/',len(ids),flush=True)
 (BASE/('sign-annotations-download.json' if '--annotations' in sys.argv else 'sign-scenes-download.json')).write_text(json.dumps(results,indent=2))
