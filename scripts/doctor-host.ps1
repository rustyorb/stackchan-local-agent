$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env.local"
if (-not (Test-Path $EnvFile)) { throw "Missing .env.local" }

$safe = @("STAKIA_LAN_HOST", "LMSTUDIO_BASE_URL", "LMSTUDIO_MODEL", "OPENROUTER_MODEL", "TZ")
$values = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $values[$Matches[1]] = $Matches[2].Trim() }
}
Write-Host "Configuration (credentials redacted):"
foreach ($name in $safe) { if ($values.ContainsKey($name)) { Write-Host "  $name=$($values[$name])" } }
foreach ($name in @("OPENROUTER_API_KEY", "OPENAI_API_KEY", "LMSTUDIO_API_KEY")) {
    $state = if ($values.ContainsKey($name) -and $values[$name]) { "set" } else { "unset" }
    Write-Host "  $name=<$state>"
}
$lan = $values["STAKIA_LAN_HOST"]
if (-not $lan -or $lan -in @("127.0.0.1", "localhost", "0.0.0.0")) { throw "STAKIA_LAN_HOST must be the PC LAN address reachable by StackChan." }

Push-Location $RepoRoot
try {
    & (Join-Path $RepoRoot ".venv\Scripts\python.exe") scripts\configure-host.py
    if ($LASTEXITCODE -ne 0) { throw "Local model/config validation failed." }
    & docker compose --env-file .env.local config --quiet
    if ($LASTEXITCODE -ne 0) { throw "Compose validation failed." }
    & docker compose --env-file .env.local ps
    try {
        $bridge = Invoke-WebRequest -Uri "http://localhost:8080/ui" -UseBasicParsing -TimeoutSec 3
        Write-Host "  bridge UI HTTP=$($bridge.StatusCode)"
    } catch { Write-Host "  bridge UI unreachable" }
    foreach ($port in @(8000)) {
        $ok = Test-NetConnection -ComputerName $lan -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
        Write-Host "  ${lan}:$port reachable=$ok"
    }
} finally { Pop-Location }
