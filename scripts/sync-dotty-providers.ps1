param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRoot,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repoRoot "third_party\dotty-stackchan\source\custom-providers"

if (-not (Test-Path -LiteralPath $sourceRoot)) {
    throw "Dotty provider source not found: $sourceRoot"
}

$targetRootFull = [System.IO.Path]::GetFullPath($TargetRoot)
$targetProviders = Join-Path $targetRootFull "custom-providers"

$items = @(
    @{ Source = "textUtils.py"; Target = "textUtils.py" },
    @{ Source = "asr"; Target = "asr" },
    @{ Source = "edge_stream"; Target = "edge_stream" },
    @{ Source = "openai_compat"; Target = "openai_compat" },
    @{ Source = "piper_local"; Target = "piper_local" },
    @{ Source = "zeroclaw"; Target = "zeroclaw" }
)

Write-Host "Source: $sourceRoot"
Write-Host "Target: $targetProviders"

if ($DryRun) {
    Write-Host "Dry run only. No files will be copied."
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $targetProviders | Out-Null
}

foreach ($item in $items) {
    $source = Join-Path $sourceRoot $item.Source
    $target = Join-Path $targetProviders $item.Target

    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing provider source: $source"
    }

    Write-Host "Sync: $($item.Source) -> $target"

    if (-not $DryRun) {
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
        Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
    }
}

Write-Host "Dotty providers synced."
