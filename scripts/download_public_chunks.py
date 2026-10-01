"""Resumable range download for public archives with interrupted long connections."""
import argparse,concurrent.futures,urllib.request,time,zipfile
from download_civic_v3 import BASE
def main():
 p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('name');a=p.parse_args()
 url=a.url
 req=urllib.request.Request(url,headers={'Range':'bytes=0-0'})
 with urllib.request.urlopen(req,timeout=45) as r:
  size=int(r.headers['Content-Range'].split('/')[-1]) if r.status==206 else int(r.headers['Content-Length'])
  resolved=r.url
 print(a.name,'bytes',size,flush=True)
 cache=BASE/(a.name+'-chunks');cache.mkdir(exist_ok=True);block=4*1024*1024
 def one(i):
  target=cache/f'{i:05}.bin';start=i*block;end=min(size,start+block)-1
  if target.exists() and target.stat().st_size==end-start+1:return
  for attempt in range(4):
   try:
    req=urllib.request.Request(resolved,headers={'Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=40) as r:
     if r.status!=206:raise ValueError('Server did not honor Range')
     raw=r.read()
    if len(raw)!=end-start+1:raise ValueError('incomplete chunk')
    target.write_bytes(raw)
    if i%10==0:print('chunk',i,flush=True)
    return
   except Exception:
    if attempt==3:raise
 count=(size+block-1)//block
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,range(count)))
 target=BASE/(a.name+'-complete.zip')
 with target.open('wb') as f:
  for i in range(count):f.write((cache/f'{i:05}.bin').read_bytes())
 out=BASE/a.name
 with zipfile.ZipFile(target) as z:
  assert all((out/n).resolve().is_relative_to(out.resolve()) for n in z.namelist())
  z.extractall(out)
  print('DONE',len(z.namelist()),z.namelist()[:5],flush=True)
if __name__=='__main__':main()
