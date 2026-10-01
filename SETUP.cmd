@echo off
cd /d "%~dp0"
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-images.txt --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto fail
call npm.cmd ci
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m ml.train
if errorlevel 1 goto fail
node node_modules\vite\bin\vite.js build
if errorlevel 1 goto fail
echo Setup complete. Double-click START_DEMO.cmd.
pause
exit /b 0
:fail
echo Setup failed. Check Python 3.11+, Node 20.19+, Internet and memory availability.
pause
exit /b 1
