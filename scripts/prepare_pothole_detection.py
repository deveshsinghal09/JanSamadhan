"""Prepare pothole detection labels from RDD D40 boxes; preserve original splits."""
import csv,json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parents[1];out=root/'data/images/pothole-detection-prepared';out.mkdir(parents=True,exist_ok=True)
with (root/'data/images/manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
counts=Counter();records=[];rejected=[]
for r in rows:
 if r['source']!='RDD2022-India' and r['label'] not in ('Garbage / litter','Waterlogging / flooded road','Other / review'):continue
 source=root/r['path'];boxes=[]
 if r['source']=='RDD2022-India':
  xml=root/'data/images/v3-sources/rdd-india/India/train/annotations/xmls'/f'{source.stem}.xml'
  tree=ET.parse(xml).getroot();w=float(tree.findtext('size/width'));h=float(tree.findtext('size/height'))
  for obj in tree.findall('object'):
   if obj.findtext('name')!='D40':continue
   b=obj.find('bndbox');x1,y1,x2,y2=[float(b.findtext(k)) for k in ('xmin','ymin','xmax','ymax')]
   if not 0<=x1<x2<=w or not 0<=y1<y2<=h:rejected.append(str(xml));continue
   boxes.append([0,(x1+x2)/(2*w),(y1+y2)/(2*h),(x2-x1)/w,(y2-y1)/h])
 labelpath=out/'labels'/r['split']/f"{r['sha256']}.txt";labelpath.parent.mkdir(parents=True,exist_ok=True)
 labelpath.write_text('\n'.join(' '.join(map(str,b)) for b in boxes))
 counts[r['split']+'_images']+=1;counts[r['split']+'_boxes']+=len(boxes)
 records.append({'image':r['path'],'labels':labelpath.relative_to(root).as_posix(),'split':r['split'],'group':r['group'],'source':r['source'],'boxes':len(boxes)})
(out/'manifest.json').write_text(json.dumps(records,indent=2));(out/'audit.json').write_text(json.dumps({'counts':dict(counts),'invalid_boxes':rejected,'policy':'RDD D40 boxes copied from original XML, not inferred from scene labels. Existing groups/splits preserved. Other civic sources are provisional negatives requiring inspection; their absence of pothole annotations is not proof of no potholes. No training or deployment yet.'},indent=2));print(json.dumps(dict(counts),indent=2))
