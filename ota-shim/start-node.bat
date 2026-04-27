@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PID_FILE=%ROOT_DIR%.stackchan-xz-node.pid"
set "LOG_FILE=%ROOT_DIR%.stackchan-xz-node.log"
set "ERR_FILE=%ROOT_DIR%.stackchan-xz-node.err.log"

if "%PORT%"=="" set "PORT=8003"
if "%HOST%"=="" set "HOST=0.0.0.0"
if "%PUBLIC_URL%"=="" set "PUBLIC_URL=http://192.168.0.250:%PORT%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pidFile = '%PID_FILE%'; $logFile = '%LOG_FILE%'; $errFile = '%ERR_FILE%'; $root = '%ROOT_DIR%';" ^
  "if (Test-Path -LiteralPath $pidFile) { $oldPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue; if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) { Write-Host \"StackChan XZ Node server already running: $oldPid\"; exit 0 } }" ^
  "$env:HOST='%HOST%'; $env:PORT='%PORT%'; $env:PUBLIC_URL='%PUBLIC_URL%';" ^
  "$p = Start-Process -FilePath node -ArgumentList @('app.js') -WorkingDirectory $root -RedirectStandardOutput $logFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden;" ^
  "Set-Content -LiteralPath $pidFile -Value $p.Id;" ^
  "Write-Host \"StackChan XZ Node server started: $($p.Id)\"; Write-Host \"Public URL: %PUBLIC_URL%\"; Write-Host \"Log: $logFile\"; Write-Host \"Error log: $errFile\""

endlocal
