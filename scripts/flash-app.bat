@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0flash-app.ps1" %*
echo.
echo Flash-app command finished.
pause
