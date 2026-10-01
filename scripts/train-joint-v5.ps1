$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& .\.venv\Scripts\python.exe -m ml.train_images --manifest data/images/v5-joint-prepared/manifest.csv --run-dir data/image-v5-joint-run --version image-v5-joint-candidate --architecture mobilenet_v3_large --image-size 384 --batch-size 4 --preserve-frame --epochs 16
if ($LASTEXITCODE -ne 0) { throw 'Joint training failed; inspect training-v5-error.log.' }
& .\.venv\Scripts\python.exe scripts/evaluate_joint_v5.py
if ($LASTEXITCODE -ne 0) { throw 'Joint evaluation failed.' }
