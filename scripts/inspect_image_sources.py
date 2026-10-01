"""Fetch public source metadata, without credentials or private application data."""
import json, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
BASE=Path(__file__).resolve().parents[1]/'data/images/v3-sources'
BASE.mkdir(parents=True,exist_ok=True)
URLS={
 'streetlights':'https://api.github.com/repos/Team16Project/Street-Light-Dataset/git/trees/main?recursive=1',
 'rdd':'https://api.figshare.com/v2/articles/21431547',
 'civic':'https://data.mendeley.com/public-api/datasets/zndzygc3p3/versions/2/files',
 'flood':'https://data.mendeley.com/public-api/datasets/t395bwcvbw/versions/1/files',
 'signs':'https://www.kaggle.com/api/v1/datasets/view/danielvareta/damaged-signs-dataset',
 'floodimg':'https://www.kaggle.com/api/v1/datasets/view/hhrclemson/flooding-image-dataset',
}
def fetch(item):
 name,url=item
 try:
  raw=urllib.request.urlopen(url,timeout=60).read();(BASE/(name+'.json')).write_bytes(raw)
  data=json.loads(raw)
  if name=='streetlights':
   from collections import Counter
   print(name,Counter('/'.join(x['path'].split('/')[:2]) for x in data['tree']),flush=True)
  elif name=='rdd':print(name,[(f['name'],f['size'],f['download_url']) for f in data['files']],flush=True)
  else: print(name,str(data)[:2200],flush=True)
 except Exception as e:print(name,type(e).__name__,str(e),flush=True)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(fetch,URLS.items()))
