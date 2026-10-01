"""Find candidate near-duplicate sign crops across source groups using dHash.
Matches request review; similarity alone does not establish identical scenes.
"""
import csv,json
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/images/v4-sign-prepared'

def main():
 with (OUT/'manifest.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
 hashes=[];pairs=[]
 for i,row in enumerate(rows):
  with Image.open(ROOT/row['path']) as im:
   small=ImageOps.exif_transpose(im).convert('L').resize((17,16));px=small.load();value=0
   for y in range(16):
    for x in range(16):value=(value<<1)|int(px[x+1,y]>px[x,y])
  for j,other in enumerate(hashes):
   distance=(value^other).bit_count()
   if distance<=4 and row['group']!=rows[j]['group']:
    pairs.append({'a':rows[j]['path'],'b':row['path'],'distance':distance,'cross_split':rows[j]['split']!=row['split'],'labels':[rows[j]['label'],row['label']]})
  hashes.append(value)
 report={'images':len(rows),'hash':'256-bit horizontal dHash','radius':4,'pairs':pairs,'cross_split_pairs':sum(p['cross_split'] for p in pairs),'policy':'Merge confirmed duplicate source groups before training; review mismatched labels. No matches does not guarantee absence of related photos.'}
 (OUT/'similarity_audit.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'images':len(rows),'candidate_pairs':len(pairs),'cross_split_pairs':report['cross_split_pairs']}))

if __name__=='__main__':main()
