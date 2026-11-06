# Simple RPi 3 Energy Hub

A standalone, smaller alternative to the parent project. The Raspberry Pi 3 is the hub and web server: it polls the PZEM Modbus slaves, serves a telemetry page, and operates the relay outputs. There is no separate Flask server or device-to-server HTTP client.

## Data and control flow

```text
PZEM slave 1 ─┐
PZEM slave 2 ─┼─ daisy-chained field bus ─ USB serial adapter ─ Raspberry Pi 3
PZEM slave 3 ─┘                                               ├─ Flask telemetry page
RFID reader ─ SPI ────────────────────────────────────────────┤
Relay inputs ◀ GPIO ───────────────────────────────────────────┘
```

The Pi polls each Modbus slave through its own USB-to-TTL adapter. The configured mapping is slave 1 → `/dev/ttyUSB1`, slave 2 → `/dev/ttyUSB0`, and slave 3 → `/dev/ttyUSB2`. PZEM meters are Modbus slaves; they do not initiate/push readings. The hub collects the readings and displays them in the browser. Web relay requests are handled on the Pi and sent to GPIO locally.

Confirm that the exact PZEM model exposes a compatible TTL Modbus interface. Use one adapter per meter as configured; do not join multiple TTL TX lines together unless the meter documentation explicitly supports that topology. Linux may renumber USB adapters after reconnecting them, so confirm the mapping with `ls -l /dev/ttyUSB*` and update `.env` if needed.

## Install and run

1. Copy `.env.example` to `.env` in this folder. Set a long random `FLASK_SECRET_KEY`, web username/password, the three PZEM port paths, relay pin assignments, and authorized RFID IDs. Do not commit `.env`.
2. On Raspberry Pi OS, create a virtual environment and install `requirements.txt`. The GPIO and RFID packages require the Pi and their hardware libraries.
3. Confirm the PZEM slave IDs and their port mapping match the installation. Defaults are ID 1 on `/dev/ttyUSB1`, ID 2 on `/dev/ttyUSB0`, and ID 3 on `/dev/ttyUSB2`, at 9600 baud, 8N1.
4. Start with outputs disconnected from loads. Run `python hub.py` and open `http://<pi-address>:5000` from a browser on the trusted LAN.
5. Check that measurements match the meters, then check relay polarity with a disconnected test load. The code assumes GPIO HIGH = relay ON and LOW = relay OFF.

The first run leaves all relays OFF. When a sensor stops reporting valid data, its corresponding relay is switched OFF and latched as tripped. Scanning the same authorized RFID card twice within five seconds clears trip latches; it **does not turn relays on**. Use the web controls to request ON after checking the fault.

## Configuration

See `.env.example`. The browser requires login. Device controls are protected by a session and CSRF token. The Flask development server is intended for a trusted lab LAN; do not expose it directly to the internet. Use HTTPS and a production WSGI server for remote access.

The power register scaling follows the parent project's existing PZEM map and can be adjusted with the `PZEM_*_SCALE` settings. Verify scaling against the exact meter model and its display before using readings for decisions. No power/overcurrent threshold is enforced in this simplified edition; it only trips on invalid/stale sensor data. Keep independent fuses/breakers and hardware protection in place.

RFID reset is disabled until `RFID_RESET_IDS` contains one or more authorized card IDs. On a Pi, the MFRC522 uses SPI. Do not use a real card ID in public documentation or source control.
