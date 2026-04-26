param(
    [string]$ServerRoot = "U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server"
)

$ErrorActionPreference = "Stop"

$python = Join-Path $ServerRoot ".venv\Scripts\python.exe"
$config = Join-Path $ServerRoot "data\.config.yaml"
$opusDir = "C:\Program Files\NoMachine\bin"

if (Test-Path -LiteralPath $python) {
    $env:PATH = "$(Split-Path -Parent $python);$env:PATH"
}

if (Test-Path -LiteralPath (Join-Path $opusDir "libopus.dll")) {
    $env:PATH = "$opusDir;$env:PATH"
}

Write-Host "ServerRoot: $ServerRoot"
Write-Host "Python:     $python"
Write-Host "Config:     $config"

if (-not (Test-Path -LiteralPath $ServerRoot)) { throw "Missing server root" }
if (-not (Test-Path -LiteralPath $python)) { throw "Missing venv python" }
if (-not (Test-Path -LiteralPath $config)) { throw "Missing local data\.config.yaml" }

& $python -c "import yaml, aiohttp, websockets, openai, edge_tts, opuslib_next, pydub; print('Python dependencies OK')"

try {
    $response = Invoke-WebRequest -Uri "http://192.168.0.250:8003/xiaozhi/ota/" -UseBasicParsing -TimeoutSec 3
    Write-Host "OTA reachable: HTTP $($response.StatusCode)"
    Write-Host ($response.Content | Select-Object -First 1)
} catch {
    Write-Host "OTA not reachable yet: $($_.Exception.Message)"
}
