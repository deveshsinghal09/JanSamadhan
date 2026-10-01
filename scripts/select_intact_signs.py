"""Record conservative human-visible contact-sheet decisions, not model labels."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/images/v4-sign-audit/intact-review'
# Indices refer to the frozen sorted index.json and sheets 0,48,...,288.
# Visible intact/readable faces only; exclude obscured, faded, vandalized,
# sticker-covered and very blurred faces. This is visual triage, not field inspection.
ACCEPT={2,3,5,6,7,11,13,20,24,25,26,31,33,34,35,38,39,41,44,
50,51,53,55,56,61,63,64,75,77,83,84,86,87,88,91,93,
98,100,101,102,104,105,106,110,118,119,121,123,125,126,129,133,137,139,140,141,143,
145,147,148,153,154,155,159,162,165,170,172,178,183,184,186,187,189,190,191,
197,198,199,200,202,203,204,207,208,210,212,214,217,220,226,227,230,232,233,237,238,
242,244,246,249,252,253,254,255,259,260,261,263,264,265,267,268,271,273,274,275,276,278,280,281,285,286,288,290,291}

def main():
 paths=json.loads((OUT/'index.json').read_text());decisions=[]
 for i,path in enumerate(paths):
  with Image.open(ROOT/path) as im:size=im.size
  accepted=i in ACCEPT and min(size)>=64
  decisions.append({'index':i,'path':Path(path).as_posix(),'decision':'intact_candidate' if accepted else 'exclude_from_intact_training',
    'reason':'Visible readable intact face at contact-sheet inspection; no obvious damage' if accepted else 'Not confidently intact at available resolution, or crop below 64 pixels',
    'width':size[0],'height':size[1]})
 result={'policy':'Visual contact-sheet triage of all 293 crops. Candidate intact labels require source/perceptual grouping with other sign data and validation before use. No claim of absence of hidden defects. Keep rejected originals unchanged.',
         'accepted':sum(d['decision']=='intact_candidate' for d in decisions),'decisions':decisions}
 (OUT/'decisions.json').write_text(json.dumps(result,indent=2));print('Intact candidates',result['accepted'],'of',len(paths))

if __name__=='__main__':main()
