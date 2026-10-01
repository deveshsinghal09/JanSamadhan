"""Inspect actual condition annotations and retain source identities for splitting."""
import csv,json,re,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/images/v4-sources/sign-defects'
OUT=ROOT/'data/images/v4-sign-audit'
LABELS=['cracked','deformation','dirty','faded','graffiti','knocked','occluded','ok','other','peeled','perforation','rust','stickers']

def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[];counts=Counter();families=defaultdict(set);examples=defaultdict(list)
 for image in sorted(BASE.glob('*/images/*')):
  if image.suffix.lower() not in ('.jpg','.jpeg','.png'):continue
  family=re.split(r'\.rf\.',image.stem)[0];split=image.parent.parent.name;families[family].add(split)
  annotation=image.parent.parent/'labels'/image.with_suffix('.txt').name
  flags=[];boxes=[]
  if not annotation.exists():flags.append('missing_annotation')
  else:
   for line in annotation.read_text().splitlines():
    if not line.strip():continue
    try:
     values=list(map(float,line.split()));cls=int(values[0])
     if len(values)!=5 or values[0]!=cls or not 0<=cls<len(LABELS) or any(not 0<=v<=1 for v in values[1:]) or min(values[3:])<=0:raise ValueError()
     boxes.append((cls,*values[1:]));counts[LABELS[cls]]+=1
    except ValueError:flags.append('invalid_box')
  if not boxes:flags.append('no_condition_box')
  try:
   with Image.open(image) as source:
    im=ImageOps.exif_transpose(source).convert('RGB');im.load()
    pixel_hash=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
    for cls,cx,cy,w,h in boxes:
     if min(w*im.width,h*im.height)<32:flags.append('tiny_condition_box')
     if len(examples[LABELS[cls]])<24 and family not in {x[0] for x in examples[LABELS[cls]]}:
      box=((cx-w/2)*im.width,(cy-h/2)*im.height,(cx+w/2)*im.width,(cy+h/2)*im.height)
      examples[LABELS[cls]].append((family,ImageOps.contain(im.crop(box),(190,145))))
  except OSError:flags.append('decode_error');pixel_hash=''
  rows.append(dict(path=image.relative_to(ROOT).as_posix(),source_family=family,original_split=split,pixel_hash=pixel_hash,labels=';'.join(sorted({LABELS[b[0]] for b in boxes})),review_flags=';'.join(sorted(set(flags)))))
 with (OUT/'inventory.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 for label,items in examples.items():
  canvas=Image.new('RGB',(1200,680),'white');draw=ImageDraw.Draw(canvas)
  for i,(family,im) in enumerate(items):
   x=i%6*200;y=i//6*170;canvas.paste(im,(x,y+22));draw.text((x,y),family[:28],fill='black')
  canvas.save(OUT/(label+'.jpg'))
 report=dict(export_images=len(rows),source_families=len(families),annotation_counts=dict(counts),source_split_overlap=[f for f,s in families.items() if len(s)>1],flags=dict(Counter(f for r in rows for f in r['review_flags'].split(';') if f)),policy='Source filename before .rf identifies augmentation family. Keep entire family in one split. Counts include augmentation, not independent originals. Condition crops require visual audit; other is not a specific defect. Multiple conditions can coexist, so do not silently force a single label.')
 (OUT/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
