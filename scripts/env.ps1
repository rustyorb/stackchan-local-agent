# Source this in a PowerShell session to activate ESP-IDF v5.5.4 and cd into firmware/:
#   . .\firmware\env.ps1
# After sourcing: idf.py, esptool.py, espefuse.py, etc. are available.
. 'C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1'
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host ''
Write-Host "StackChan firmware env ready — cwd: $(Get-Location)" -ForegroundColor Cyan
