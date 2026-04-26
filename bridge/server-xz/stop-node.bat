@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PID_FILE=%ROOT_DIR%.stackchan-xz-node.pid"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pidFile = '%PID_FILE%';" ^
  "if (!(Test-Path -LiteralPath $pidFile)) { Write-Host 'StackChan XZ Node server is not running'; exit 0 }" ^
  "$serverPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue;" ^
  "if ($serverPid -and (Get-Process -Id $serverPid -ErrorAction SilentlyContinue)) { Stop-Process -Id $serverPid -Force; Write-Host \"StackChan XZ Node server stopped: $serverPid\" } else { Write-Host 'StackChan XZ Node server pid was stale' }" ^
  "Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue"

endlocal
