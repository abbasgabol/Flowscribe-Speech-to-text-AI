@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not finish. See the message above and try again.
  pause
  exit /b 1
)
exit /b 0
