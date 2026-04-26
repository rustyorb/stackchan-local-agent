@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor-real-server.ps1" %*
