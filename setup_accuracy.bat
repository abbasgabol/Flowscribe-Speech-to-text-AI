@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run setup.bat first.
 pause
 exit /b 1
)
.venv\Scripts\python.exe download_accuracy_model.py
if errorlevel 1 (
 echo Accuracy model setup failed. See the error above.
 pause
 exit /b 1
)
echo Ready. Select Accuracy in Local Dictation.
pause
