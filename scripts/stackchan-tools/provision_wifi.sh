#!/usr/bin/env bash
# Provision StackChan via NVS, bypassing the BLE app entirely.
# Usage:
#   SSID=<ssid> PASSWORD=<pass> [OTA_URL=<url>] ./tools/provision_wifi.sh [PORT]
# Defaults: PORT=COM5
#
# Writes the NVS partition at 0x9000 with:
#   namespace 'wifi'
#     ssid / password         (SsidManager picks these up)
#     ota_url                 (only if OTA_URL is set; overrides CONFIG_OTA_URL)
#   namespace 'app_config'
#     is_configed = 1         (skip BLE setup flow on boot)
set -eu

: "${SSID:?SSID env var required}"
: "${PASSWORD:?PASSWORD env var required}"
: "${OTA_URL:=}"

PORT="${1:-COM5}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR_WIN="$(cygpath -w "$PROJECT_DIR" 2>/dev/null || (cd "$PROJECT_DIR" && pwd -W))"

# Use a local temp dir so PowerShell can read the paths directly (no cygwin
# path translation).
TMP_DIR="$PROJECT_DIR/tools/.provision-tmp"
mkdir -p "$TMP_DIR"
CSV="$TMP_DIR/nvs.csv"
BIN="$TMP_DIR/nvs.bin"
CSV_WIN="$(cygpath -w "$CSV" 2>/dev/null || echo "$CSV")"
BIN_WIN="$(cygpath -w "$BIN" 2>/dev/null || echo "$BIN")"
trap 'rm -rf "$TMP_DIR"' EXIT

# Escape , and " for NVS CSV (values can contain spaces but no raw commas/quotes)
if printf '%s' "$SSID$PASSWORD" | grep -qE '[,"]' ; then
  echo "error: SSID or PASSWORD contains a comma or double-quote; edit this script to quote them properly" >&2
  exit 2
fi

{
  echo "key,type,encoding,value"
  echo "wifi,namespace,,"
  echo "ssid,data,string,$SSID"
  echo "password,data,string,$PASSWORD"
  if [ -n "$OTA_URL" ]; then
    if printf '%s' "$OTA_URL" | grep -qE '[,"]' ; then
      echo "error: OTA_URL contains a comma or quote; csv-escape needed" >&2
      exit 2
    fi
    echo "ota_url,data,string,$OTA_URL"
  fi
  echo "app_config,namespace,,"
  echo "is_configed,data,u8,1"
} > "$CSV"

# NVS partition is 0x4000 bytes per the partition table
NVS_SIZE=0x4000
NVS_OFFSET=0x9000

# Use the v5.5.4 IDF's nvs_partition_gen via our pwsh wrapper environment.
# Run everything in a single pwsh invocation so the v5.5.4 env is loaded once.
echo "[provision] generating NVS blob"
pwsh -NoProfile -NoLogo -Command "
  Remove-Item env:MSYSTEM -ErrorAction SilentlyContinue
  Remove-Item env:MSYSCON -ErrorAction SilentlyContinue
  Remove-Item env:MSYS -ErrorAction SilentlyContinue
  Remove-Item env:VIRTUAL_ENV -ErrorAction SilentlyContinue
  Remove-Item env:_OLD_VIRTUAL_PATH -ErrorAction SilentlyContinue
  Remove-Item env:VIRTUAL_ENV_PROMPT -ErrorAction SilentlyContinue
  . 'C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1' | Out-Null
  python \"C:\esp\v5.5.4\esp-idf\components\nvs_flash\nvs_partition_generator\nvs_partition_gen.py\" generate '$CSV_WIN' '$BIN_WIN' '$NVS_SIZE'
  if (\$LASTEXITCODE -ne 0) { exit \$LASTEXITCODE }
" >&2

echo "[provision] flashing NVS partition at $NVS_OFFSET on $PORT"
pwsh -NoProfile -NoLogo -Command "
  Remove-Item env:MSYSTEM -ErrorAction SilentlyContinue
  Remove-Item env:MSYSCON -ErrorAction SilentlyContinue
  Remove-Item env:MSYS -ErrorAction SilentlyContinue
  Remove-Item env:VIRTUAL_ENV -ErrorAction SilentlyContinue
  Remove-Item env:_OLD_VIRTUAL_PATH -ErrorAction SilentlyContinue
  Remove-Item env:VIRTUAL_ENV_PROMPT -ErrorAction SilentlyContinue
  . 'C:\Espressif\tools\Microsoft.v5.5.4.PowerShell_profile.ps1' | Out-Null
  python -m esptool --chip esp32s3 --port '$PORT' --after hard_reset write_flash '$NVS_OFFSET' '$BIN_WIN'
  if (\$LASTEXITCODE -ne 0) { exit \$LASTEXITCODE }
" >&2

echo "[provision] done — device hard-reset, should auto-join '$SSID' on next boot"
