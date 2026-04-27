@echo off
REM Build the StackChan custom firmware via ESP-IDF v5.5.4 Docker image.
REM
REM Output: firmware/xiaozhi-esp32/build/merged-binary.bin
REM
REM Usage:
REM   firmware\build.bat                  (uses LAN_IP from env, falls back to 192.168.178.100)
REM   firmware\build.bat 192.168.1.42     (override LAN IP for OTA URL)
REM
REM Requirements:
REM   - Docker Desktop running
REM   - espressif/idf:v5.5.4 image present (run: docker pull espressif/idf:v5.5.4)
REM   - firmware/xiaozhi-esp32/ checked out (run: git clone https://github.com/78/xiaozhi-esp32.git firmware/xiaozhi-esp32)

setlocal enabledelayedexpansion

REM Resolve LAN IP — argument > env var > hardcoded fallback.
set "LAN_IP=%~1"
if "!LAN_IP!"=="" set "LAN_IP=%LAN_IP%"
if "!LAN_IP!"=="" set "LAN_IP=192.168.178.100"

set "REPO_ROOT=%~dp0.."
set "FW_ROOT=%REPO_ROOT%\firmware\xiaozhi-esp32"

if not exist "%FW_ROOT%\CMakeLists.txt" (
    echo ERROR: %FW_ROOT% does not look like a checked-out xiaozhi-esp32 tree.
    echo Run: git clone https://github.com/78/xiaozhi-esp32.git "%FW_ROOT%"
    exit /b 1
)

REM Materialise sdkconfig.local from the override template, substituting LAN_IP.
echo [build] writing sdkconfig.local with LAN_IP=!LAN_IP!
powershell -NoProfile -Command "(Get-Content '%REPO_ROOT%\firmware\sdkconfig.override') -replace '__LAN_IP__','!LAN_IP!' | Set-Content '%FW_ROOT%\sdkconfig.local' -Encoding utf8"

echo [build] running ESP-IDF v5.5.4 build for m5stack-core-s3 (target esp32s3)
docker run --rm ^
    -v "%FW_ROOT%:/project" ^
    -w /project ^
    espressif/idf:v5.5.4 ^
    bash -lc "git config --global --add safe.directory '*' && idf.py set-target esp32s3 && idf.py -DBOARD_TYPE=m5stack-core-s3 build && idf.py merge-bin"

if errorlevel 1 (
    echo [build] FAILED
    exit /b 1
)

echo.
echo [build] OK
echo Output: %FW_ROOT%\build\merged-binary.bin
echo To flash: firmware\flash.bat
