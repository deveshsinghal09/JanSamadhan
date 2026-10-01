$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& .\.venv\Scripts\python.exe -m ml.train_images --manifest data/images/v4-electrical-prepared/manifest.csv --run-dir data/image-v4-electrical-recovery --version image-v4-electrical-candidate --architecture mobilenet_v3_small --image-size 224 --batch-size 8 --preserve-frame --epochs 16 --init-checkpoint data/image-v4-electrical-run/ml/image_model.pt
if ($LASTEXITCODE -ne 0) { throw 'Electrical training failed; inspect training-v4-error.log.' }
& .\.venv\Scripts\python.exe -m ml.train_images --manifest data/images/v4-parking-prepared/manifest.csv --run-dir data/image-v4-parking-run --version image-v4-parking-candidate --architecture mobilenet_v3_small --image-size 224 --batch-size 8 --preserve-frame --epochs 16
if ($LASTEXITCODE -ne 0) { throw 'Parking training failed; inspect training-v4-error.log.' }
