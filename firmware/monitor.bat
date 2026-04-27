@echo off
REM Tail the StackChan's serial console at 115200 baud.
REM
REM Usage:
REM   firmware\monitor.bat            (uses COM5)
REM   firmware\monitor.bat COM7
REM
REM Press Ctrl+] to exit pyserial-miniterm.

setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM5"

set "REPO_ROOT=%~dp0.."
set "PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: project venv not found at %PYTHON%
    exit /b 1
)

echo [monitor] tailing %PORT% at 115200 baud — Ctrl+] exits
"%PYTHON%" -m serial.tools.miniterm %PORT% 115200
