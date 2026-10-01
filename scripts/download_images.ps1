$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
New-Item -ItemType Directory -Force data/images | Out-Null
$datasetRef='programmerrdai/road-issues-detection-dataset'
Invoke-WebRequest -Uri ('https://www.kaggle.com/api/v1/datasets/view/'+$datasetRef) -OutFile data/images/programmerrdai.json
Write-Host 'Downloading ~500 MB for local academic evaluation. See docs/IMAGE_MODEL_REVIEW.md for source and licensing limitations.'
Invoke-WebRequest -Uri ('https://www.kaggle.com/api/v1/datasets/download/'+$datasetRef) -OutFile data/images/road-issues.zip
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/garythung/trashnet/master/LICENSE' -OutFile data/images/TRASHNET_LICENSE.txt
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/garythung/trashnet/master/data/dataset-resized.zip' -OutFile data/images/trashnet.zip
Write-Host 'Download complete. Run TRAIN_IMAGES.cmd.'
