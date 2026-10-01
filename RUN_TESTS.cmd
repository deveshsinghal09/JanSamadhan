@echo off
cd /d "%~dp0"
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
if errorlevel 1 goto fail
node --test --test-concurrency=1 tests/api.test.js
if errorlevel 1 goto fail
echo All tests passed.
pause
exit /b 0
:fail
echo Tests failed. Make sure the AI service is started.
pause
exit /b 1
