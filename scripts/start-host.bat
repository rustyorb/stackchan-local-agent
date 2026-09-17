@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-host.ps1" %*
