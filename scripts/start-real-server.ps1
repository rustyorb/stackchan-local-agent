param(
    [string]$ServerRoot = "U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot ".runtime"
$pidFile = Join-Path $runtimeDir "xiaozhi-server.pid"
$outLog = Join-Path $runtimeDir "xiaozhi-server.log"
$errLog = Join-Path $runtimeDir "xiaozhi-server.err.log"

function Test-PortInUse {
    param([int]$Port)
    $matches = netstat -ano | Select-String -Pattern "LISTENING\s+\d+$" | Where-Object {
        $_.Line -match "[:.]$Port\s"
    }
    return [bool]$matches
}

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue
    if ($existingPid -and (Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue)) {
        Write-Host "XiaoZhi server already running: $existingPid"
        Write-Host "OTA: http://192.168.0.250:8003/xiaozhi/ota/"
        exit 0
    }
}

if (-not (Test-Path -LiteralPath $ServerRoot)) {
    throw "Server checkout not found: $ServerRoot"
}

& (Join-Path $PSScriptRoot "install-real-server-gui.ps1") -ServerRoot $ServerRoot

$python = Join-Path $ServerRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python venv not found: $python"
}

$venvScripts = Split-Path -Parent $python
$env:PATH = "$venvScripts;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$opusDir = "C:\Program Files\NoMachine\bin"
if (Test-Path -LiteralPath (Join-Path $opusDir "libopus.dll")) {
    $env:PATH = "$opusDir;$env:PATH"
}

$config = Join-Path $ServerRoot "data\.config.yaml"
if (-not (Test-Path -LiteralPath $config)) {
    throw "Local server config missing: $config"
}

foreach ($port in @(8000, 8003)) {
    if (Test-PortInUse -Port $port) {
        throw "Port $port is already in use. Stop the old bridge/server before starting this one."
    }
}

$process = Start-Process `
    -FilePath $python `
    -ArgumentList "app.py" `
    -WorkingDirectory $ServerRoot `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ASCII
Start-Sleep -Seconds 2

if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Start-Sleep -Seconds 1
    $listenerPids = netstat -ano | Select-String -Pattern ":(8000|8003)\s+.*LISTENING\s+(\d+)" | ForEach-Object {
        if ($_.Line -match "LISTENING\s+(\d+)") { $Matches[1] }
    } | Select-Object -Unique
    if ($listenerPids) {
        Set-Content -LiteralPath $pidFile -Value ($listenerPids | Select-Object -First 1) -Encoding ASCII
    }
    try {
        Invoke-WebRequest -Uri "http://192.168.0.250:8003/api/restart-needed" -Method Post -UseBasicParsing -TimeoutSec 3 | Out-Null
    } catch {
        Write-Host "Admin restart flag could not be cleared yet: $($_.Exception.Message)"
    }
    Write-Host "XiaoZhi server started: $(Get-Content -LiteralPath $pidFile)"
    Write-Host "Admin GUI: http://192.168.0.250:8003/"
    Write-Host "OTA: http://192.168.0.250:8003/xiaozhi/ota/"
    Write-Host "WebSocket: ws://192.168.0.250:8000/xiaozhi/v1/"
    Write-Host "Log: $outLog"
    Write-Host "Error log: $errLog"
} else {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "XiaoZhi server failed to stay running."
    if (Test-Path -LiteralPath $errLog) {
        Get-Content -LiteralPath $errLog -Tail 80
    }
    exit 1
}
