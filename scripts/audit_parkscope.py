"""Audit original parking photographs, annotations and acquisition leakage.

Quality flags request visual review; they do not silently delete night photos.
Category codes remain codes until their semantic mapping is verified.
"""
import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/images/v4-sources/parkscope'
OUT=ROOT/'data/images/v4-parking-audit'

def inspect(path):
    match=re.fullmatch(r'S(\d+)E(\d+)V(\d+)P(\d+)C(\d+)',path.stem)
    if not match:raise ValueError(f'Unrecognized original filename: {path.name}')
    scene,illumination,vehicle,view,category=match.groups()
    row=dict(path=path.relative_to(ROOT).as_posix(),scene=scene,illumination=illumination,
        vehicle=vehicle,view=view,category_code=category,original_split=path.parent.parent.name)
    annotation=path.parent.parent/'labels'/path.with_suffix('.txt').name
    flags=[];classes=Counter()
    if not annotation.exists():flags.append('missing_annotation')
    else:
        for line in annotation.read_text().splitlines():
            if not line.strip():continue
            values=list(map(float,line.split()))
            if len(values)<7 or (len(values)-1)%2 or values[0] not in (0,1,2,3) or any(v<0 or v>1 for v in values[1:]):
                flags.append('invalid_polygon');continue
            classes[str(int(values[0]))]+=1
        if not classes.get('3'):flags.append('no_annotated_vehicle')
    try:
        with Image.open(path) as source:
            image=ImageOps.exif_transpose(source).convert('RGB');image.load()
            row.update(width=image.width,height=image.height,
                pixel_hash=hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest())
            gray=np.asarray(image.convert('L').resize((128,128)),dtype=np.float32)
            lap=-4*gray[1:-1,1:-1]+gray[2:,1:-1]+gray[:-2,1:-1]+gray[1:-1,2:]+gray[1:-1,:-2]
            row.update(sharpness=round(float(lap.var()),3),mean_luminance=round(float(gray.mean()),3))
            if min(image.size)<128:flags.append('small_image')
            if gray.mean()<15:flags.append('very_dark_review')
            if lap.var()<12:flags.append('low_detail_review')
    except OSError:flags.append('decode_error')
    row['annotation_counts']=json.dumps(classes,sort_keys=True)
    row['review_flags']=';'.join(sorted(set(flags)))
    return row

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files=sorted(p for p in BASE.glob('*/images/*.jpg'))
    if len(files)!=6000:raise ValueError(f'Incomplete archive: {len(files)} of 6000 photos')
    with ThreadPoolExecutor(max_workers=1) as pool:rows=list(pool.map(inspect,files))
    vehicles=defaultdict(list);pixels=defaultdict(list)
    for row in rows:
        vehicles[row['vehicle']].append(row)
        if row.get('pixel_hash'):pixels[row['pixel_hash']].append(row)
    conflicts=[key for key,group in vehicles.items() if len({r['category_code'] for r in group})!=1]
    report={'images':len(rows),'unique_vehicle_ids':len(vehicles),
        'category_codes':dict(Counter(r['category_code'] for r in rows)),
        'scene_counts':dict(Counter(r['scene'] for r in rows)),
        'vehicle_category_conflicts':conflicts,
        'vehicle_split_overlap':sum(len({r['original_split'] for r in group})>1 for group in vehicles.values()),
        'duplicate_pixel_groups':sum(len(group)>1 for group in pixels.values()),
        'duplicate_pixel_split_overlap':sum(len({r['original_split'] for r in group})>1 for group in pixels.values()),
        'quality_flags':dict(Counter(flag for row in rows for flag in row['review_flags'].split(';') if flag)),
        'policy':'Flags require visual review, not automatic deletion. Keep all views of each vehicle together. Prefer scene-separated evaluation. Code-to-description mapping remains unverified; do not train named parking violations by guessing.',
        'source':'https://github.com/Nanasaki-Ai/ParkScope'}
    fields=sorted({key for row in rows for key in row})
    with (OUT/'inventory.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
