"""Acquire published defect photographs without changing the deployed dataset."""
import concurrent.futures
import json
import urllib.request
import urllib.parse
from pathlib import Path
from download_civic_v3 import download

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/images/v4-sources'

def inspection():
    repo = 'SFStefenon/InspectionDataSet'
    BASE.mkdir(parents=True, exist_ok=True)
    source_root = BASE / 'inspection'
    source_root.mkdir(exist_ok=True)
    source_root = source_root.resolve()
    tree_path = BASE / 'inspection-tree.json'
    download(f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1', tree_path)
    entries = json.loads(tree_path.read_text())['tree']
    entries = [e for e in entries if e['type'] == 'blob' and
               (e['path'].startswith(('Defective/', 'Normal/', 'YOLO')) or e['path'] == 'README.md')]
    def one(entry):
        relative = entry['path']
        target = source_root / relative
        if not target.resolve().is_relative_to(source_root):
            raise ValueError('Unsafe source path')
        url = f'https://raw.githubusercontent.com/{repo}/main/' + urllib.parse.quote(relative)
        download(url, target)
        return {'path': relative, 'git_blob': entry['sha'], 'url': url}
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for record in pool.map(one, entries):
            records.append(record)
            if len(records) % 40 == 0:
                print('Inspection files', len(records), '/', len(entries), flush=True)
    (BASE / 'inspection-download.json').write_text(json.dumps(records, indent=2))
    print('Inspection download complete:', len(records), flush=True)

if __name__ == '__main__':
    inspection()
