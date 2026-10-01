"""Download only the labelled supervised fault subset, retaining original labels."""
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from download_civic_v3 import download

base=Path(__file__).resolve().parents[1]/'data/images/v4-sources'
samples=json.loads((base/'insplad-samples.json').read_text())['samples']
samples=[s for s in samples if s.get('task')=='fault_classification']
out=base/'insplad';out.mkdir(exist_ok=True);out=out.resolve()
for parent in {str(Path(s['filepath']).parent) for s in samples}:
    candidate=out/parent
    if Path(parent).is_absolute() or '..' in Path(parent).parts:raise ValueError('Unsafe source directory')
    candidate.mkdir(parents=True,exist_ok=True)
    if not candidate.resolve().is_relative_to(out):raise ValueError('Unsafe resolved directory')
records=[]
def one(s):
    path=s['filepath'];target=out/path
    if Path(path).is_absolute() or '..' in Path(path).parts:raise ValueError('Unsafe source path')
    url='https://huggingface.co/datasets/Voxel51/InsPLAD/resolve/main/'+quote(path)
    record={'path':path,'asset':s['asset'],'label':s['fault']['label'],'original_split':s['tags'][-1],'url':url}
    try:download(url,target)
    except Exception as error:record['error']=str(error)
    return record
print('Supervised fault images',len(samples),'labels',dict(Counter(s['fault']['label'] for s in samples)),flush=True)
with ThreadPoolExecutor(max_workers=12) as pool:
    for record in pool.map(one,samples):
        records.append(record)
        if len(records)%100==0:
            print('Downloaded',len(records),'/',len(samples),'errors',sum('error' in r for r in records),flush=True)
            (base/'insplad-download.json').write_text(json.dumps(records,indent=2))
(base/'insplad-download.json').write_text(json.dumps(records,indent=2))
print('DONE',len(records),flush=True)
