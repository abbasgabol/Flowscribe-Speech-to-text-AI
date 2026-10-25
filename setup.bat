@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe download_model.py
if errorlevel 1 goto failed
.venv\Scripts\python.exe download_punctuation.py
if errorlevel 1 goto failed
echo Setup complete. Open run.bat to start.
pause
exit /b 0
:failed
echo Setup failed. Check the error above.
pause
exit /b 1
