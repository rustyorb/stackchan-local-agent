@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor.ps1" -NoFlash %*
echo.
echo Monitor exited.
pause
