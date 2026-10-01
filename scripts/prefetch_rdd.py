import concurrent.futures,json,urllib.request,zipfile,time
from download_rdd_subset import BASE,RemoteZip
record=json.loads((BASE/'rdd.json').read_text());f=next(f for f in record['files'] if f['name'].endswith('.zip'))
r=RemoteZip(f['download_url'],f['size'])
with zipfile.ZipFile(r) as z:info=z.getinfo('RDD2022/India.zip')
first=info.header_offset//r.block;last=(info.header_offset+info.compress_size+4096)//r.block
print('India blocks',first,last,flush=True)
missing=[i for i in range(first,last+1) if not (r.cache/f'{i:05}.bin').exists()]
# The sequential downloader owns the next two missing blocks.
def one(i):
 path=r.cache/f'{i:05}.bin'
 if path.exists():return
 for attempt in range(4):
  try:
   start=i*r.block;end=min(start+r.block,r.size)-1
   req=urllib.request.Request(r.url,headers={'Range':f'bytes={start}-{end}'})
   with urllib.request.urlopen(req,timeout=40) as response:
    if response.status!=206:raise ValueError('range unavailable')
    raw=response.read()
   if len(raw)!=end-start+1:raise ValueError('incomplete block')
   temp=path.with_suffix('.prefetch');temp.write_bytes(raw);temp.replace(path)
   print('block',i,'saved',flush=True);return
  except Exception as e:
   if attempt==3:print('block failed',i,str(e),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,missing[2:]))
