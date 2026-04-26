"""Minimal serial-port tail for the StackChan device.

Usage: python tools/serial_tail.py [PORT] [BAUD]
Default port COM5, baud 115200. Ctrl-C to stop.
"""
import sys
import time
import serial

port = sys.argv[1] if len(sys.argv) > 1 else "COM5"
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

def open_port():
    # On ESP32-S3 USB-Serial/JTAG, DTR+RTS get translated into the GPIO0/EN
    # boot-mode handshake. Setting either one before/at open can knock the
    # device into ROM download mode. Pass the current control-line state
    # through unchanged.
    return serial.Serial(
        port=port,
        baudrate=baud,
        timeout=1,
        write_timeout=1,
        dsrdtr=False,
        rtscts=False,
    )

print(f"[serial_tail] opening {port} @ {baud}...", flush=True)
while True:
    try:
        s = open_port()
        break
    except serial.SerialException as e:
        print(f"[serial_tail] retry ({e})", flush=True)
        time.sleep(1)

print(f"[serial_tail] connected", flush=True)
buf = b""
while True:
    try:
        data = s.read(1024)
    except serial.SerialException as e:
        # Device reset / USB re-enumerated — reopen.
        print(f"[serial_tail] read failed, reopening ({e})", flush=True)
        try:
            s.close()
        except Exception:
            pass
        while True:
            try:
                s = open_port()
                break
            except serial.SerialException as e2:
                print(f"[serial_tail] reopen retry ({e2})", flush=True)
                time.sleep(1)
        continue
    except KeyboardInterrupt:
        print("[serial_tail] stopped", flush=True)
        break
    if not data:
        continue
    buf += data
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        print(line.decode(errors="replace").rstrip("\r"), flush=True)
