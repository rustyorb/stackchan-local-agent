param([switch]$Build)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot ".env.local"
if (-not (Test-Path $EnvFile)) { throw "Create .env.local from .env.local.example first." }

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Missing .venv. Run: py -m venv .venv; .venv\Scripts\pip install -r bridge\requirements.txt" }

Push-Location $RepoRoot
try {
    & $Python scripts\configure-host.py
    if ($LASTEXITCODE -ne 0) { throw "Configuration rendering failed." }
    $args = @("compose", "--env-file", ".env.local", "up", "-d")
    if ($Build) { $args += "--build" }
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed." }

    $runtime = Join-Path $RepoRoot ".runtime"
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    $pidFile = Join-Path $runtime "bridge.pid"
    $running = $false
    if (Test-Path $pidFile) {
        $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($oldPid -and (Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue)) { $running = $true }
    }
    if (-not $running) {
        $proc = Start-Process -FilePath $Python -ArgumentList "bridge.py" -WorkingDirectory $RepoRoot `
            -RedirectStandardOutput (Join-Path $runtime "bridge.log") `
            -RedirectStandardError (Join-Path $runtime "bridge.err.log") -WindowStyle Hidden -PassThru
        Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
        Write-Host "Bridge started: PID $($proc.Id), UI http://localhost:8080/ui"
    } else { Write-Host "Bridge already running: PID $oldPid" }
} finally { Pop-Location }
