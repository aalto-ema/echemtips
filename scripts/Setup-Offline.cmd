@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-Offline.ps1"
if errorlevel 1 (
  echo Setup failed. Read the message above; do not connect hardware yet.
  pause
  exit /b 1
)
echo Setup complete. Use the eChemTips desktop shortcuts or Start eChemTips.vbs.
pause
