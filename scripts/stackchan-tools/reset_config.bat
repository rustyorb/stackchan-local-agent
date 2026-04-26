@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset_config.ps1" %*
echo.
echo Reset-config command finished.
pause
