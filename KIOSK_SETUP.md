# RFID access-control kiosk

The MPI3508 uses its HDMI connection for video. The kiosk page runs in a browser on the Raspberry Pi and uses the existing Flask web session and RC522 reader; it does not need a separate display driver.

## Requirements

- The Flask app is updated and its database schema is migrated with `flask --app app init-db`.
- `main.py` is running on the Raspberry Pi and its `API_BASE_URL` points to the Flask server.
- The Pi's `.env` contains the authorized card IDs in `RFID_RESET_IDS`, the shared `DEVICE_API_TOKEN`, and `BASELINE_MODE=0` when relay control is intended.
- An administrator account is available for the browser session.

## Open the kiosk

1. On the Raspberry Pi browser, sign in to the web dashboard as an administrator.
2. Select **KIOSK** in the dashboard header, or open `/kiosk` on the same Flask host.
3. For a full-screen session, launch Chromium with the Flask server address:

   ```bash
   chromium --kiosk --noerrdialogs --disable-infobars http://<FLASK_HOST>:5000/kiosk
   ```

   Sign in as an administrator in that browser profile first so its Flask session is available to the kiosk page.

## RFID flow

1. While locked, the display shows the date and clock, a daily reflection, an energy tip, and **Scan your RFID Card**.
2. Scan an authorized card once. The kiosk unlocks for five minutes and shows current branch readings, sensor status, and any latched trip.
3. Inspect the displayed branches. Scan the **same authorized card** again to confirm. The device records a local reset snapshot; telemetry samples continue to be retained in the Flask database.
4. The interface returns to locked standby after the confirmed scan. If the five-minute inspection period expires, it re-locks without resetting trips.

## Reset behavior

- A per-branch daily energy-limit trip resets that branch's daily budget. Only branches that were requested ON before cutoff are automatically restored. The Pi keeps the meter's cumulative counter as the new baseline, so additional energy is counted after reset.
- A system-wide instantaneous power cutoff clears its latch but leaves the affected branches OFF. Reduce the load, then use the administrator dashboard to request ON.
- A sensor-fault trip remains latched and OFF until the sensor problem is fixed.
- The Pi's `BASELINE_MODE=1` setting always holds all relay outputs OFF, regardless of kiosk reset. Use `BASELINE_MODE=0` only when relay operation is intended and the installation has been checked.
- Card IDs are not written to the reset audit record.
