param(
    [string]$ServerRoot = "U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".runtime\xiaozhi-server.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    $serverPid = $null
} else {
    $serverPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue
}

if ($serverPid -and (Get-Process -Id ([int]$serverPid) -ErrorAction SilentlyContinue)) {
    Stop-Process -Id ([int]$serverPid) -Force
    Write-Host "XiaoZhi server stopped: $serverPid"
} else {
    if ($serverPid) {
        Write-Host "XiaoZhi server pid file was stale: $serverPid"
    }
}

$listenerPids = netstat -ano | Select-String -Pattern ":(8000|8003)\s+.*LISTENING\s+(\d+)" | ForEach-Object {
    if ($_.Line -match "LISTENING\s+(\d+)") { $Matches[1] }
} | Select-Object -Unique

foreach ($listenerPid in $listenerPids) {
    if (Get-Process -Id ([int]$listenerPid) -ErrorAction SilentlyContinue) {
        Stop-Process -Id ([int]$listenerPid) -Force
        Write-Host "Stopped listener pid: $listenerPid"
    }
}

Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
