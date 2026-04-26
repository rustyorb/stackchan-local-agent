@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-real-server-gui.ps1" %*
