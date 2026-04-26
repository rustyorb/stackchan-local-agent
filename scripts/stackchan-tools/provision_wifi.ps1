param(
    [string]$Ssid = "",

    [string]$Password = "",

    [string]$OtaUrl = "",

    [string]$Port = "COM5"
)

$ErrorActionPreference = "Stop"

if (!$Ssid) {
    $Ssid = Read-Host "Wi-Fi SSID"
}

if (!$Password) {
    $securePassword = Read-Host "Wi-Fi password" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    try {
        $Password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

foreach ($value in @($Ssid, $Password, $OtaUrl)) {
    if ($value -match '[,"]') {
        throw "SSID, password, and OTA URL cannot contain commas or double-quotes in this simple CSV writer."
    }
}

$projectDir = Split-Path -Parent $PSScriptRoot
$tmpDir = Join-Path $projectDir "tools\.provision-tmp"
$csvPath = Join-Path $tmpDir "nvs.csv"
$binPath = Join-Path $tmpDir "nvs.bin"
$nvsSize = "0x4000"
$nvsOffset = "0x9000"
$profile = "C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1"
$nvsGen = "C:\esp\v5.5.4\esp-idf\components\nvs_flash\nvs_partition_generator\nvs_partition_gen.py"

New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

$lines = @(
    "key,type,encoding,value",
    "wifi,namespace,,",
    "ssid,data,string,$Ssid",
    "password,data,string,$Password"
)

if ($OtaUrl) {
    $lines += "ota_url,data,string,$OtaUrl"
}

$lines += @(
    "app_config,namespace,,",
    "is_configed,data,u8,1"
)

Set-Content -LiteralPath $csvPath -Value $lines -Encoding ascii

Write-Host "[provision] generating NVS blob"
. $profile | Out-Null
python $nvsGen generate $csvPath $binPath $nvsSize
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[provision] flashing NVS partition at $nvsOffset on $Port"
python -m esptool --chip esp32s3 --port $Port --after hard_reset write_flash $nvsOffset $binPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[provision] done; device reset and should auto-join '$Ssid'"
