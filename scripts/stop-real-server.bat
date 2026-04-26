@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-real-server.ps1" %*
