# StackChan Custom Firmware

Builds a customised xiaozhi-esp32 firmware that points at our local
xiaozhi-esp32-server (Docker on this PC) instead of the cloud default.

## How it works

The upstream `xiaozhi-esp32` firmware exposes the OTA endpoint as a
**build-time Kconfig string** (`CONFIG_OTA_URL`, default
`https://api.tenclass.net/xiaozhi/ota/`). On boot, the device GETs that
URL and the response carries the WebSocket address it should connect to.

Our local `xiaozhi-esp32-server` container hosts an OTA endpoint at
`http://<LAN_IP>:8003/xiaozhi/ota/` that returns
`ws://<LAN_IP>:8000/xiaozhi/v1/`. So all we need is to override
`CONFIG_OTA_URL` at build time. **No code patch.**

## Files

- `sdkconfig.override` — Kconfig overrides applied on every build. The
  `__LAN_IP__` token is substituted at build time.
- `build.bat` — runs `idf.py` inside the `espressif/idf:v5.5.4` Docker
  image against `firmware/xiaozhi-esp32/`. Outputs
  `xiaozhi-esp32/build/merged-binary.bin`.
- `flash.bat` — uses `esptool` (in the project venv) to write the binary
  to the device over USB-C at 921600 baud.
- `monitor.bat` — tails the serial console at 115200 baud.
- `xiaozhi-esp32/` — the upstream firmware source (gitignored — clone
  with `git clone https://github.com/78/xiaozhi-esp32.git firmware/xiaozhi-esp32`).

## First-boot

```powershell
# 0. One-time setup (already done if you ran the project bootstrap)
docker pull espressif/idf:v5.5.4
git clone https://github.com/78/xiaozhi-esp32.git firmware\xiaozhi-esp32
.venv\Scripts\python.exe -m pip install esptool pyserial

# 1. Build (15–25 min cold, faster on subsequent runs because IDF caches)
firmware\build.bat                    # auto-detects LAN IP fallback
firmware\build.bat 192.168.178.100    # or pass it explicitly

# 2. Put the StackChan into download mode: hold RST for 3 seconds
#    (screen stays blank/dark; device shows up as USB-Serial/JTAG)

# 3. Flash
firmware\flash.bat                    # uses COM5
firmware\flash.bat COM7               # override

# 4. Watch it boot
firmware\monitor.bat
```

## What this firmware does NOT include yet

The dotty-derived patch (perception event producers, custom state
machine, LED contract overrides, suppressed activation digit voice) was
specific to dotty's setup and stale against upstream v2.2.6. We're
starting from a stock build with **only** the OTA-URL override, so:

- **No face_detected / sound_event perception events** to the bridge —
  the bridge's perception consumers will be inert until firmware emits them
- Servo head-turn from sound localization works only if upstream supports it
- Activation flow plays the digit-by-digit voice prompt (annoying but
  harmless)

These are deliberate omissions for first-boot simplicity. Layered on
later by writing fresh patches against current upstream, not by trying
to apply dotty's stale one.
