param(
    [string]$Port = "COM5"
)

$ErrorActionPreference = "Stop"

$Python = "C:\Espressif\tools\python\v5.5.4\venv\Scripts\python.exe"
$NvsOffset = "0x9000"
$NvsSize = "0x4000"

if (!(Test-Path $Python)) {
    throw "ESP-IDF Python not found: $Python"
}

$env:PYTHONHASHSEED = "0"

Write-Host "Erasing StackChan NVS config on $Port..." -ForegroundColor Cyan
Write-Host "Region: offset $NvsOffset, size $NvsSize"
& $Python -m esptool --chip esp32s3 --port $Port --before default_reset --after hard_reset erase_region $NvsOffset $NvsSize
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Done. Wi-Fi/app config is reset; firmware should return to provisioning/config flow." -ForegroundColor Green
