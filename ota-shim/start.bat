@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PID_FILE=%ROOT_DIR%.stackchan-xz.pid"
set "LOG_FILE=%ROOT_DIR%.stackchan-xz.log"
set "ERR_FILE=%ROOT_DIR%.stackchan-xz.err.log"

if "%PUBLIC_URL%"=="" set "PUBLIC_URL=http://192.168.0.250:8003"
if "%HOST%"=="" set "HOST=0.0.0.0"
if "%PORT%"=="" set "PORT=8003"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pidFile = '%PID_FILE%'; $logFile = '%LOG_FILE%'; $errFile = '%ERR_FILE%'; $root = '%ROOT_DIR%';" ^
  "if (Test-Path -LiteralPath $pidFile) { $oldPid = Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue; if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) { Write-Host \"StackChan XZ server already running: $oldPid\"; exit 0 } }" ^
  "$args = @('app.py','--host','%HOST%','--port','%PORT%','--public-url','%PUBLIC_URL%');" ^
  "$p = Start-Process -FilePath python -ArgumentList $args -WorkingDirectory $root -RedirectStandardOutput $logFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden;" ^
  "Set-Content -LiteralPath $pidFile -Value $p.Id;" ^
  "Write-Host \"StackChan XZ server started: $($p.Id)\"; Write-Host \"Public URL: %PUBLIC_URL%\"; Write-Host \"Log: $logFile\"; Write-Host \"Error log: $errFile\""

endlocal
