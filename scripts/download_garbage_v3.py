import concurrent.futures,json,zipfile,urllib.request
from download_civic_v3 import BASE,download
def archive(name,url):
 try:
  path=BASE/(name+'.zip');download(url,path)
  with zipfile.ZipFile(path) as z:
   out=BASE/name
   for member in z.namelist():
    if not (out/member).resolve().is_relative_to(out.resolve()):raise ValueError('unsafe member')
   z.extractall(out)
   print(name,'files',len(z.namelist()),'sample',z.namelist()[:12],flush=True)
 except Exception as e:print(name,str(e),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  jobs=[pool.submit(archive,'garbage-piles','https://www.kaggle.com/api/v1/datasets/download/hammadarshad18/garbage-detection'),pool.submit(archive,'gini','https://codeload.github.com/spotgarbage/spotgarbage-GINI/zip/refs/heads/master')]
  for f in jobs:f.result()
