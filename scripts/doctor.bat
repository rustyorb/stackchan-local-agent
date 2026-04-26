@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor.ps1" %*
echo.
echo Doctor finished or monitor exited.
pause
