param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
function Ready($url) { try { return (Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2).StatusCode -eq 200 } catch { return $false } }
if (!(Test-Path '.venv\Scripts\python.exe') -or !(Test-Path 'dist\index.html') -or !(Test-Path 'ml\models.joblib')) { throw 'Run SETUP.cmd first: an environment, build or model file is missing.' }
if (!(Ready 'http://127.0.0.1:8001/health')) {
 Start-Process -FilePath "$projectRoot\.venv\Scripts\python.exe" -ArgumentList '-m','uvicorn','ml.service:app','--host','127.0.0.1','--port','8001' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot\data\ai.log" -RedirectStandardError "$projectRoot\data\ai-error.log"
}
if (!(Ready 'http://127.0.0.1:3001/api/health')) {
 Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList ('"'+$projectRoot+'\backend\server.js"') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot\data\api.log" -RedirectStandardError "$projectRoot\data\api-error.log"
}
$ready = $false
for ($i=0; $i -lt 30; $i++) {
 if ((Ready 'http://127.0.0.1:8001/health') -and (Ready 'http://127.0.0.1:3001/api/health')) { $ready=$true; break }
 Start-Sleep -Seconds 1
}
if (!$ready) { throw 'Services did not start. Read data\ai-error.log and data\api-error.log. Close memory-heavy applications and retry.' }
Write-Host 'Ready: http://127.0.0.1:3001 | Demo password: Review@123'
if (!$NoBrowser) { Start-Process 'http://127.0.0.1:3001' }

