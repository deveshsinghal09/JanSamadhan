"""Download only explicitly annotated GINI images; never label by query alone."""
import csv,json,urllib.parse,concurrent.futures
from download_civic_v3 import BASE,download
labels={r['image']:r for r in csv.DictReader((BASE/'gini-labels.csv').open()) if r['label'] in ('0','1')}
tree=json.loads((BASE/'gini-tree.json').read_text())['tree']
selected=[x for x in tree if x['path'].split('/')[-1] in labels and '/garbage-queried-images/' in x['path']]
def one(x):
 try:
  download('https://raw.githubusercontent.com/spotgarbage/spotgarbage-GINI/master/'+urllib.parse.quote(x['path']),BASE/'gini-labeled'/x['path'])
  return {'path':x['path'],'git_blob':x['sha'],'label':labels[x['path'].split('/')[-1]]['label']}
 except Exception as e:return {'path':x['path'],'error':str(e)}
if __name__=='__main__':
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
  for result in pool.map(one,selected):
   results.append(result)
   if len(results)%100==0:print('GINI',len(results),'/',len(selected),flush=True)
 (BASE/'gini-download.json').write_text(json.dumps(results,indent=2));print('GINI done',len(results),flush=True)
