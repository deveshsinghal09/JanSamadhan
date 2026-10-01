"""Build detector-ready layout using only original RDD box annotations."""
import json,os
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parents[1];prepared=root/'data/images/pothole-detection-prepared'
rows=[r for r in json.loads((prepared/'manifest.json').read_text()) if r['source']=='RDD2022-India']
out=root/'data/images/pothole-detector-rdd';counts=Counter();groups={}
for r in rows:
 split=r['split'];assert groups.setdefault(r['group'],split)==split
 image=root/r['image'];label=root/r['labels'];name=label.stem
 target=out/'images'/split/(name+image.suffix.lower());target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():os.link(image,target)
 targetlabel=out/'labels'/split/(name+'.txt');targetlabel.parent.mkdir(parents=True,exist_ok=True)
 targetlabel.write_text(label.read_text())
 counts[split+'_images']+=1;counts[split+'_boxes']+=r['boxes']
config='path: '+out.as_posix()+'\ntrain: images/train\nval: images/validation\ntest: images/test\nnames:\n  0: pothole\n'
(out/'dataset.yaml').write_text(config)
(out/'audit.json').write_text(json.dumps({'counts':dict(counts),'groups':len(groups),'policy':'Only original RDD India D40 annotations. Non-RDD provisional negatives excluded until audited. Hard links preserve source bytes. Splits unchanged. No Newport diagnostic image included. Detection background means no annotated D40; other road damage may be present.'},indent=2))
print(json.dumps(dict(counts),indent=2))
