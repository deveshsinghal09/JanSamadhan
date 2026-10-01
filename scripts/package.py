import zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
output=root/'JanSamadhan_Review_Package.zip'
folders=['backend','frontend','ml','data','docs','scripts','tests','dist']
files=['.env.example','README.md','package.json','package-lock.json','requirements.txt','requirements-images.txt','vite.config.js','index.html','.gitignore','START_DEMO.cmd','SETUP.cmd','RUN_TESTS.cmd']
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for name in files:z.write(root/name,arcname='JanSamadhan/'+name)
 for folder in folders:
  for p in (root/folder).rglob('*'):
   if any(part.startswith(('image-v4-','image-v5-','image-v6-')) for part in p.parts) or p.name=='pixel_cache.json':continue
   if not p.is_file() or '__pycache__' in p.parts or 'runtime' in p.parts or any(x in p.parts for x in ('image-v2-run','image-v3-run','image-v4-road-run','image-v4-road-recovery','v3-sources','v4-sources','archive','clip-pretrained','pothole-detector-rdd','pothole-detector-runs')) or p.name=='hash-cache.json' or p.suffix=='.log':continue
   if 'images' in p.parts and ('raw' in p.parts or 'demo' in p.parts or 'torch-cache' in p.parts or p.suffix=='.zip' or p.name in ('source_contact_sheet.jpg','taco_audit_sheet.jpg')):continue
   z.write(p,arcname='JanSamadhan/'+p.relative_to(root).as_posix())
print(str(output),output.stat().st_size,'bytes')
