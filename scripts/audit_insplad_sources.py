"""Audit source capture identities before using InsPLAD component crops.

Metadata-only: can run while downloads continue. No prediction-based filtering.
"""
import csv,json,re
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/images/v4-sources'
OUT=ROOT/'data/images/v4-electrical-audit'

def source_identity(filename):
    # Every component crop/augmentation from one camera exposure stays together.
    match=re.search(r'^(.*?DJI_\d+)',filename,re.I)
    if not match: return None,None
    capture=match.group(1)
    date=re.search(r'(\d{2}-\d{2}-\d{4})',capture)
    return capture,date.group(1) if date else None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((BASE/'insplad-samples.json').read_text())['samples']
    selected=[s for s in metadata if s.get('task')=='fault_classification']
    rows=[];captures=defaultdict(list);dates=defaultdict(Counter)
    for s in selected:
        path=Path(s['filepath']);capture,date=source_identity(path.name)
        row={'path':(BASE/'insplad'/path).relative_to(ROOT).as_posix(),
             'asset':s['asset'],'condition':s['fault']['label'],
             'original_split':s['tags'][-1],'capture_id':capture or '',
             'capture_date':date or '', 'downloaded':(BASE/'insplad'/path).exists()}
        rows.append(row)
        if capture:captures[capture].append(row)
        if date:dates[date][row['condition']]+=1
    overlap=[k for k,v in captures.items() if len({r['original_split'] for r in v})>1]
    report={'metadata_rows':len(rows),'downloaded_files':sum(r['downloaded'] for r in rows),
      'capture_ids':len(captures),'capture_dates':len(dates),
      'unparsed_capture_ids':sum(not r['capture_id'] for r in rows),
      'unparsed_dates':sum(not r['capture_date'] for r in rows),
      'original_split_capture_overlap':len(overlap),
      'conditions':dict(Counter(r['condition'] for r in rows)),
      'capture_date_conditions':{k:dict(v) for k,v in sorted(dates.items())},
      'policy':'Counts are component crops and can include augmented variants. Group by original camera capture, acquisition date and image similarity before splitting. Original split names do not prove independence. Missing downloads are pending, not rejected images. Conditions are missing caps, rust and nests; not all electrical faults.'}
    with (OUT/'source_inventory.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (OUT/'source_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='capture_date_conditions'},indent=2))

if __name__=='__main__':main()
