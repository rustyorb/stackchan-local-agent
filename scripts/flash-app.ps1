param(
    [string]$Port = "COM5",
    [string]$AppBin = ""
)

$ErrorActionPreference = "Stop"

$FirmwareDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Espressif\tools\python\v5.5.4\venv\Scripts\python.exe"
if (!$AppBin) {
    $AppBin = Join-Path $FirmwareDir "build\stack-chan.bin"
}

if (!(Test-Path $Python)) {
    throw "ESP-IDF Python not found: $Python"
}
if (!(Test-Path $AppBin)) {
    throw "App binary not found: $AppBin"
}

$env:PYTHONHASHSEED = "0"

Write-Host "Flashing StackChan app slot only..." -ForegroundColor Cyan
Write-Host "Port: $Port"
Write-Host "App:  $AppBin"
& $Python -m esptool --chip esp32s3 --port $Port --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB 0x20000 $AppBin
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Done. App slot flashed and device reset." -ForegroundColor Green
