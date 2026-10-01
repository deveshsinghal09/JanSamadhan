"""Reproducible, numbered contact sheets for visual source-label auditing."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import random,json
BASE=Path(__file__).resolve().parents[1]/'data/images/v3-sources'
out=BASE/'audit';out.mkdir(exist_ok=True)
random.seed(42)
for source in BASE.iterdir():
 if not source.is_dir() or source==out:continue
 paths=[p for p in source.rglob('*') if p.suffix.lower() in ('.jpg','.jpeg','.png')]
 if not paths:continue
 sample=random.sample(paths,min(24,len(paths)))
 canvas=Image.new('RGB',(1200,((len(sample)+5)//6)*190),'white');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(sample):
  x=(i%6)*200;y=(i//6)*190
  try:
   with Image.open(p) as im:canvas.paste(ImageOps.contain(im.convert('RGB'),(195,155)),(x,y+30))
   draw.text((x,y),str(i)+' '+p.parent.name[:24],fill='black')
   draw.text((x,y+14),p.name[:27],fill='black')
  except Exception as e:draw.text((x,y+50),str(e)[:20],fill='red')
 canvas.save(out/(source.name+'.jpg'))
 (out/(source.name+'.json')).write_text(json.dumps([str(p) for p in sample],indent=2))
 print(source.name,len(paths),flush=True)
