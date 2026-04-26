param(
    [string]$Port = "COM5",
    [switch]$NoFlash
)

$ErrorActionPreference = "Stop"

$FirmwareDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $FirmwareDir
$Profile = "C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1"
$LogDir = Join-Path $RepoRoot "logs"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "stackchan-monitor-$Stamp.log"

if (!(Test-Path $Profile)) {
    throw "ESP-IDF v5.5.4 profile not found: $Profile"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "StackChan firmware doctor" -ForegroundColor Cyan
Write-Host "Firmware: $FirmwareDir"
Write-Host "Port:     $Port"
Write-Host "Log:      $LogFile"
Write-Host ""

. $Profile | Out-Null
Set-Location -LiteralPath $FirmwareDir

Write-Host "Checking target..." -ForegroundColor Cyan
idf.py set-target esp32s3

Write-Host ""
Write-Host "Building firmware..." -ForegroundColor Cyan
idf.py build

if (!$NoFlash) {
    Write-Host ""
    Write-Host "Flashing app and starting monitor..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+] to exit monitor." -ForegroundColor Yellow
    idf.py -p $Port flash monitor 2>&1 | Tee-Object -FilePath $LogFile
} else {
    Write-Host ""
    Write-Host "NoFlash set; starting monitor only..." -ForegroundColor Cyan
    Write-Host "Press Ctrl+] to exit monitor." -ForegroundColor Yellow
    idf.py -p $Port monitor 2>&1 | Tee-Object -FilePath $LogFile
}
