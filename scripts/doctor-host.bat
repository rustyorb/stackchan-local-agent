@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor-host.ps1" %*
