import csv,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
BASE=Path(__file__).resolve().parents[1]/'data/images/v3-sources'
paths={p.name:p for p in (BASE/'gini').rglob('*.jpg') if 'garbage-queried-images' in p.parts}
for label in ('1','0'):
 rows=[r for r in csv.DictReader((BASE/'gini-labels.csv').open()) if r['label']==label and r['image'] in paths]
 for start in range(0,len(rows),48):
  selected=rows[start:start+48];c=Image.new('RGB',(1200,((len(selected)+7)//8)*120),'white');d=ImageDraw.Draw(c)
  for j,r in enumerate(selected):
   x=j%8*150;y=j//8*120
   with Image.open(paths[r['image']]) as im:c.paste(ImageOps.contain(im.convert('RGB'),(147,98)),(x,y+18))
   d.text((x,y),str(start+j),fill='black')
  c.save(BASE/'audit'/f'gini-{label}-{start:03}.jpg')
 (BASE/'audit'/f'gini-{label}-index.json').write_text(json.dumps(rows,indent=2))
