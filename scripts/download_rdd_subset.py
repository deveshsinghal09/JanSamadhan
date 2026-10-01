"""Read the official Figshare ZIP by HTTP range; download only Indian data."""
import io,json,urllib.request,zipfile
from download_civic_v3 import BASE
class RemoteZip(io.RawIOBase):
 def __init__(self,url,size):
  self.url=url;self.size=size;self.pos=0;self.block=8*1024*1024
  self.cache=BASE/'rdd-range-cache';self.cache.mkdir(exist_ok=True)
 def seekable(self):return True
 def readable(self):return True
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
  return self.pos
 def tell(self):return self.pos
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  n=min(n,self.size-self.pos);parts=[]
  while n>0:
   index=self.pos//self.block;start=index*self.block;end=min(start+self.block,self.size)-1
   path=self.cache/f'{index:05}.bin'
   if not path.exists():
    req=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=90) as r:
     if r.status!=206:raise ValueError('Server does not support byte ranges')
     raw=r.read()
    if len(raw)!=end-start+1:raise ValueError('Incomplete range')
    path.write_bytes(raw)
   raw=path.read_bytes();offset=self.pos-start;take=min(n,len(raw)-offset)
   parts.append(raw[offset:offset+take]);self.pos+=take;n-=take
  return b''.join(parts)
if __name__=='__main__':
 record=json.loads((BASE/'rdd.json').read_text());f=next(f for f in record['files'] if f['name'].endswith('.zip'))
 with zipfile.ZipFile(RemoteZip(f['download_url'],f['size'])) as z:
  names=z.namelist();(BASE/'rdd-file-list.json').write_text(json.dumps(names))
  selected=[n for n in names if 'india' in n.lower() and not n.endswith('/')]
  print('Selected',len(selected),'files; examples',selected[:8],flush=True)
  out=BASE/'rdd-india'
  for i,name in enumerate(selected):
   target=out/name
   if not target.resolve().is_relative_to(out.resolve()):raise ValueError('unsafe member')
   if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
   if i%500==0:print('RDD',i,'/',len(selected),flush=True)
