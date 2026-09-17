# Stakia expressive-eye build

Use this for the commercial M5Stack StackChan K151/K151-R with original controller. The older `build.bat` targets generic CoreS3 and is retained as historical tooling, not the recommended Stakia build.

Mars already has a stock restore option. No stock rebuild is required.

## On your Windows computer

Open the terminal supplied by your installed ESP-IDF, then check:

```powershell
idf.py --version
Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Name
```

The pinned factory source requires ESP-IDF **5.5.4**. Mars’s screenshot shows **6.1** installed; install 5.5.4 alongside it and open the 5.5.4 terminal for this build. Confirm the USB port; The screenshot lists **COM15 as USB Serial Device**. Confirm this is Stakia by unplugging/reconnecting her and checking which port disappears/returns. If no serial port appears, inspect Device Manager and check the USB data cable.

From the root of this project:

```powershell
python -m pip install "cryptography>=46,<47"
python firmware/build_factory.py --eyes stakia --server-host YOUR_PC_LAN_IP
```

This clones factory commit `1b5765599fba8aaad1811d9a79358ccc7051f5f3`, applies the eye patch, fetches the factory's specified dependencies, checks all required patches, and builds in `firmware/StackChan/firmware/build-stakia`. It uses your installed ESP-IDF and does not flash automatically.

Replace `YOUR_PC_LAN_IP` with your computer's private IPv4 address, for example `192.168.1.20`. Keep that address stable with a router DHCP reservation.

This build connects directly to `wss://YOUR_PC_LAN_IP:8000/xiaozhi/v1/`. It bypasses vendor OTA/bootstrap and activation entirely. Old saved vendor URLs and tokens are ignored. There is no vendor fallback if the local server is unavailable. Model selection happens on your host; OpenRouter is used only when you select it.

The helper generates or reuses `data/security/`, embeds the public local CA and robot credential, and forces certificate verification in the isolated sdkconfig. It does not embed the server private key. Use the same security directory for the PC host and firmware build. Credentials and generated firmware must remain private. Certificates expire after 825 days; regeneration requires rebuilding/reflashing the paired robot.

The firmware uses the hardware RTC for TLS date validation, with its build time as a lower bound if the RTC was reset. Keep the hardware clock correct; this lower bound is not a replacement for a maintained RTC. No public time service is contacted. The ESP network component is pinned to 3.6.4, whose TLS implementation attaches the configured CA bundle.

The launcher retains AI, local ESP-NOW control, BLE dance, and local hardware settings. Vendor account, community/app-center, and EzData functions are unavailable. Wi-Fi setup uses the device's local configuration access point. Public NTP, camera uploads, network firmware upgrades, and asset downloads are disabled. Time comes from the hardware RTC until local time synchronization is added.

The build downloads open-source dependencies on your PC. That is separate from robot runtime traffic; a physical network capture remains part of bench verification.

## Download mode

Connect a data-capable USB cable to the robot's base. Hold RST beside the microSD slot for approximately three seconds, then release when the LED turns green. It goes out when download mode is entered. [M5Stack instructions](https://docs.m5stack.com/en/StackChan#download-mode)

Files on the removable card do not replace USB firmware flashing.

## After a successful build and a verified port

From the factory firmware directory, with the ESP-IDF terminal active:

```powershell
cd firmware/StackChan/firmware
idf.py -B build-stakia -D SDKCONFIG=build-stakia/sdkconfig -p COM15 flash monitor
```

Use COM15 only if verified on your computer. This is the actual device-write step. No erase-flash command is needed. Exit the monitor with Ctrl+].

## What the eye patch includes

- 96 × 108 pixel normal eye regions with white sclera and emerald irises.
- Dark pupils and highlights; gaze shifts inside the eyes.
- Independent lids driven by the existing blink/expression system.
- Six factory emotion mappings, including asymmetric skeptical eyes.
- Smaller mouth moved down to fit the larger eyes.
- Existing hardware, touch, audio, and motion implementation retained.

It currently uses a fixed emerald color; runtime palette controls and audio-driven lip synchronization are later integrations. No SD-card assets are required for this renderer.

## Verification available here

The geometry test exercises sizing, gaze boundaries, complete blink closure, and negative rotation normalization. The native-build helper tests rejection of public/loopback endpoints. The patch is checked against the exact factory revision.

The full ESP-IDF firmware has **not** been compiled in this workspace, which has no ESP-IDF installation. Rendering performance and appearance still need validation on the physical display. Do not mistake these host checks for a completed firmware build.
