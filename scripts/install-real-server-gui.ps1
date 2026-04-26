param(
    [string]$ServerRoot = "U:\_Projects\xiaozhi-esp32-server\main\xiaozhi-server"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $repoRoot "real-server\local_admin"
$targetDir = Join-Path $ServerRoot "local_admin"
$httpServer = Join-Path $ServerRoot "core\http_server.py"
$connectionServer = Join-Path $ServerRoot "core\connection.py"
$openaiProvider = Join-Path $ServerRoot "core\providers\llm\openai\openai.py"
$pythonForPatch = Join-Path $ServerRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $sourceDir)) {
    throw "GUI source not found: $sourceDir"
}

if (-not (Test-Path -LiteralPath $httpServer)) {
    throw "XiaoZhi HTTP server file not found: $httpServer"
}

if (-not (Test-Path -LiteralPath $connectionServer)) {
    throw "XiaoZhi connection file not found: $connectionServer"
}

if (-not (Test-Path -LiteralPath $openaiProvider)) {
    throw "XiaoZhi OpenAI provider file not found: $openaiProvider"
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -Path (Join-Path $sourceDir "*") -Destination $targetDir -Recurse -Force

$patcher = @'
from pathlib import Path
import sys

http_path = Path(sys.argv[1])
connection_path = Path(sys.argv[2])
openai_path = Path(sys.argv[3])
content = http_path.read_text(encoding="utf-8-sig")

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

http_path.write_text(content, encoding="utf-8")

connection = connection_path.read_text(encoding="utf-8-sig")
local_bind_patch = (
    "            # 在后台初始化配置和组件（完全不阻塞主循环）\n"
    "            if not self.read_config_from_api:\n"
    "                self.need_bind = False\n"
    "                self.bind_completed_event.set()\n\n"
    "            asyncio.create_task(self._background_initialize())\n"
)
if local_bind_patch not in connection:
    connection = connection.replace(
        "            # 在后台初始化配置和组件（完全不阻塞主循环）\n"
        "            asyncio.create_task(self._background_initialize())\n",
        local_bind_patch,
    )
connection_path.write_text(connection, encoding="utf-8")

openai_provider = openai_path.read_text(encoding="utf-8-sig")
compat_method = '''    def _apply_model_compatibility(self, request_params: dict):
        """Normalize OpenAI-compatible parameters for newer model families."""
        model_name = (self.model_name or "").lower()
        if model_name.startswith("gpt-5"):
            max_tokens = request_params.pop("max_tokens", None)
            if max_tokens is not None:
                request_params["max_completion_tokens"] = max_tokens
            request_params.pop("temperature", None)
            request_params.pop("top_p", None)
            request_params.pop("frequency_penalty", None)

'''
if "def _apply_model_compatibility" not in openai_provider:
    openai_provider = openai_provider.replace(
        "    def response(self, session_id, dialogue, **kwargs):\n",
        compat_method + "    def response(self, session_id, dialogue, **kwargs):\n",
    )
if "self._apply_model_compatibility(request_params)" not in openai_provider:
    openai_provider = openai_provider.replace(
        "        self._apply_thinking_disabled(request_params)\n\n        responses = self.client.chat.completions.create(**request_params)\n",
        "        self._apply_thinking_disabled(request_params)\n        self._apply_model_compatibility(request_params)\n\n        responses = self.client.chat.completions.create(**request_params)\n",
    )
    openai_provider = openai_provider.replace(
        "        self._apply_thinking_disabled(request_params)\n\n        stream = self.client.chat.completions.create(**request_params)\n",
        "        self._apply_thinking_disabled(request_params)\n        self._apply_model_compatibility(request_params)\n\n        stream = self.client.chat.completions.create(**request_params)\n",
    )
openai_path.write_text(openai_provider, encoding="utf-8")
'@

if (Test-Path -LiteralPath $pythonForPatch) {
    $patcher | & $pythonForPatch - $httpServer $connectionServer $openaiProvider
} else {
    $patcher | python - $httpServer $connectionServer $openaiProvider
}

Write-Host "Installed StackChan admin GUI into: $targetDir"
Write-Host "Patched HTTP routes in: $httpServer"
Write-Host "Patched local-mode bind timing in: $connectionServer"
Write-Host "Patched GPT-5 token compatibility in: $openaiProvider"
