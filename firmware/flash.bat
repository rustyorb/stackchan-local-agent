@echo off
REM Flash the merged firmware binary to the StackChan over USB-C.
REM
REM Usage:
REM   firmware\flash.bat            (uses COM5)
REM   firmware\flash.bat COM7       (override COM port)
REM
REM Before running:
REM   1. Build the firmware: firmware\build.bat
REM   2. Put device in download mode: hold RST for 3 seconds. The device
REM      should appear as a USB-Serial/JTAG endpoint, and the screen will
REM      stay black/blank (the bootloader doesn't update the display).
REM
REM esptool lives in the project venv (.venv\Scripts\python.exe -m esptool).

setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=COM5"

set "REPO_ROOT=%~dp0.."
set "FW_BIN=%REPO_ROOT%\firmware\xiaozhi-esp32\build\merged-binary.bin"
set "PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%FW_BIN%" (
    echo ERROR: firmware binary not found at %FW_BIN%
    echo Run: firmware\build.bat
    exit /b 1
)

if not exist "%PYTHON%" (
    echo ERROR: project venv not found at %PYTHON%
    echo Run: python -m venv .venv ^&^& .venv\Scripts\python.exe -m pip install esptool
    exit /b 1
)

echo [flash] flashing %FW_BIN% to %PORT% at 921600 baud
"%PYTHON%" -m esptool --chip esp32s3 --port %PORT% --baud 921600 ^
    write_flash 0x0 "%FW_BIN%"

if errorlevel 1 (
    echo [flash] FAILED — confirm the device is in download mode (hold RST 3s) and PORT is correct
    exit /b 1
)

echo.
echo [flash] OK — device should reboot into the new firmware
echo Watch boot log: firmware\monitor.bat (or use any serial tool at 115200 baud)
