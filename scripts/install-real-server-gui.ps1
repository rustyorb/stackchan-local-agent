param(
    [string]$ServerRoot = "U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $repoRoot "real-server\local_admin"
$targetDir = Join-Path $ServerRoot "local_admin"
$httpServer = Join-Path $ServerRoot "core\http_server.py"
$pythonForPatch = Join-Path $ServerRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $sourceDir)) {
    throw "GUI source not found: $sourceDir"
}

if (-not (Test-Path -LiteralPath $httpServer)) {
    throw "XiaoZhi HTTP server file not found: $httpServer"
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -Path (Join-Path $sourceDir "*") -Destination $targetDir -Recurse -Force

$patcher = @'
from pathlib import Path
import sys

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8-sig")

if "from local_admin.admin import setup_admin_routes" not in content:
    content = content.replace(
        "from core.api.vision_handler import VisionHandler\n",
        "from core.api.vision_handler import VisionHandler\n\n"
        "try:\n"
        "    from local_admin.admin import setup_admin_routes\n"
        "except Exception:\n"
        "    setup_admin_routes = None\n",
    )

if "setup_admin_routes(app)" not in content:
    content = content.replace(
        "                app = web.Application()\n",
        "                app = web.Application()\n\n"
        "                if setup_admin_routes:\n"
        "                    setup_admin_routes(app)\n",
    )

path.write_text(content, encoding="utf-8")
'@

if (Test-Path -LiteralPath $pythonForPatch) {
    $patcher | & $pythonForPatch - $httpServer
} else {
    $patcher | python - $httpServer
}

Write-Host "Installed StackChan admin GUI into: $targetDir"
Write-Host "Patched HTTP routes in: $httpServer"
