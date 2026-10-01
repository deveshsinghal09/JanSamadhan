"""Reproducible v3 training; never overwrites the deployed checkpoint."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 subprocess.run([sys.executable,'-u','-m','ml.prepare_civic_v3'],cwd=ROOT,check=True)
 subprocess.run([sys.executable,'-u','-m','ml.train_images','--manifest','data/images/v3-prepared/manifest.csv','--run-dir','data/image-v3-run','--version','image-v3','--epochs','16'],cwd=ROOT,check=True)
