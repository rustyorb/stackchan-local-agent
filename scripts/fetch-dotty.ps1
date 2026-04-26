param(
    [string]$Destination = "third_party\dotty-stackchan"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutRoot = Join-Path $RepoRoot $Destination
$BaseUrl = "https://raw.githubusercontent.com/BrettKinny/dotty-stackchan/main"

$Files = @(
    "LICENSE",
    ".config.yaml",
    "SETUP.md",
    "README.md",
    "custom-providers/openai_compat/__init__.py",
    "custom-providers/openai_compat/openai_compat.py",
    "custom-providers/asr/whisper_local.py",
    "custom-providers/asr/fun_local.py",
    "custom-providers/piper_local/piper_local.py",
    "custom-providers/edge_stream/edge_stream.py",
    "custom-providers/zeroclaw/zeroclaw.py",
    "custom-providers/textUtils.py",
    "docs/architecture.md",
    "docs/voice-pipeline.md",
    "docs/protocols.md"
)

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

foreach ($File in $Files) {
    $Target = Join-Path $OutRoot ($File -replace "/", "\")
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    $Url = "$BaseUrl/$File"
    Write-Host "Fetching $File"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Target
}

Write-Host ""
Write-Host "Dotty reference files written to $OutRoot" -ForegroundColor Green
