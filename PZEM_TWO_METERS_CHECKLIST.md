# PZEM Slave 1 and 2 Troubleshooting Checklist

Use this checklist later to test the two PZEM-004T meters that are not showing readings. The goal is to test one physical meter at a time, identify the Modbus ID that actually answers, and then return the Pi to continuous monitoring.

## Important safety and setup notes

- PZEM-004T meters may be connected to mains voltage. Only change wiring when the meter and the circuit are fully de-energized. If you are not trained to work with mains wiring, have a qualified person isolate and reconnect the meter.
- Use the USB-to-TTL adapter's USB connection to the Pi. Do not connect a TTL signal directly to the Pi's GPIO pins.
- UART data lines cross: adapter TX goes to PZEM RX; adapter RX goes to PZEM TX. Connect adapter GND to PZEM GND.
- Do not connect adapter 5V to the PZEM unless the exact PZEM documentation says to power it that way. The PZEM may need its own documented supply.
- Each PZEM currently has its own USB-to-TTL adapter. Do not join multiple TTL TX outputs together unless the exact meter documentation explicitly supports that topology.
- `main.py` and `pzem_multi_reader.py` both use the serial adapter. Never run both at the same time.
- Configured mapping: slave 1 → `/dev/ttyUSB1`, slave 2 → `/dev/ttyUSB0`, slave 3 → `/dev/ttyUSB2`.

## Before the meeting / notes to collect

Write down these details if known:

- Pi project folder: ______________________________
- USB adapter device shown by the Pi: ______________________________
- Meter labels/model: ______________________________
- Meter A intended ID: ______
- Meter B intended ID: ______
- Which meter is currently known to answer as ID 3: ______________________________

Keep a result table while testing:

| Physical meter tested alone | ID 1 result | ID 2 result | ID 3 result | Notes |
|---|---|---|---|---|
| Meter A | | | | |
| Meter B | | | | |
| Known responding meter (optional) | | | | |

Record the actual voltage/current/power result or the full timeout/error text. A meter that returns data under a different ID than expected may have a different saved address.

## Part A — Check continuous monitoring and stop it cleanly

1. Connect to the Raspberry Pi terminal/SSH session where you started `main.py`.
2. If it is currently displaying `Sensor readings:`, press **Ctrl+C once**. This stops the continuous reader so the test program can use the USB serial port.
3. Confirm it stopped:

   ```bash
   pgrep -af 'main.py'
   ```

   If the command still prints a `python3 main.py` process, return to the terminal that started it and press **Ctrl+C** there. Do not start the one-shot reader while `main.py` still owns the adapter.
4. This project did not show a dedicated PZEM systemd service in the service list you pasted. Do not stop unrelated services such as `glamor-test.service`.

## Part B — Find the USB serial device

5. In the Pi terminal, go to the project directory. Replace the example path with the real directory:

   ```bash
   cd ~/path/to/your/project
   ```

6. Check that the adapters appear:

   ```bash
   ls -l /dev/ttyUSB* /dev/serial/by-id/
   ```

   The configured mapping is slave 1 → `/dev/ttyUSB1`, slave 2 → `/dev/ttyUSB0`, slave 3 → `/dev/ttyUSB2`. Linux may assign different numbers after reconnecting adapters; update the code mapping if the actual assignment changes.
7. If any expected `/dev/ttyUSB*` device is missing, reconnect that adapter and check the listing again before diagnosing the PZEM address.

## Part C — Test Meter A by itself

8. Ensure `main.py` is stopped and the USB adapter is not being used by another reader.
9. Fully de-energize Meter A and its measurement circuit before changing its communication wires. Disconnect the other PZEM meters from the TTL communication connection so only Meter A is attached.
10. Confirm the TTL wiring:

    - USB-TTL TX → Meter A RX
    - USB-TTL RX → Meter A TX
    - USB-TTL GND → Meter A GND
    - USB-TTL 5V → leave disconnected unless the exact meter documentation instructs otherwise

11. Restore power only after the wiring is secure and it is safe to do so. Keep clear of exposed mains terminals.
12. From the project directory, run:

    ```bash
    python3 pzem_multi_reader.py
    ```

13. The program lists available slave IDs. Enter **1** first. Record whether it prints numeric measurements or an error. A timeout means it did not receive a valid reply from ID 1 on that attempt.
14. When asked `Test another branch? [y/N]:`, enter `y`, then test **2**, and then **3**. Record each result in the table. This checks whether the meter is actually answering at a different address than expected.
15. Once all three IDs have been tested for Meter A, enter `n` to exit the reader.
16. If Meter A answers at one ID, record that as its responding ID. Do not change the address yet.

## Part D — Test Meter B by itself

17. Fully de-energize Meter B and its measurement circuit before changing the communication wires.
18. Disconnect Meter A and connect only Meter B to the USB-TTL adapter, using the same crossed TX/RX and common GND wiring.
19. Restore power only when wiring is secure and safe.
20. Run the reader again:

    ```bash
    python3 pzem_multi_reader.py
    ```

21. Test IDs **1**, **2**, and **3** in that order, recording the results. Exit with `n` after testing all three.
22. Compare Meter A and Meter B results. Each meter should answer under its own intended, unique ID. If both answer under the same ID when tested alone, they currently have duplicate addresses and should not be put together on a shared bus until addressed correctly.

## Part E — If an individual meter times out at every ID

23. Stop the reader with `n` or **Ctrl+C**.
24. With the circuit fully de-energized, recheck that only the intended meter is on the TTL wires and that TX/RX are crossed and GND is common.
25. Check the meter's exact model/manual to confirm its communication pins are TTL UART and its baud/framing match the reader's **9600 baud, 8 data bits, no parity, 1 stop bit (9600 8N1)**.
26. Check that the meter is powered according to its documentation. Do not use the adapter's 5V pin as a guessed power source.
27. If possible, reconnect the known responding Meter 3 using the same adapter and wiring and test ID 3. If ID 3 works but the other meter still fails alone, the adapter and Pi port are likely working; focus on the nonresponding meter's power, pin labels/wiring, exact model/protocol, or actual saved address.
28. Save the full error text for each failed ID. Do not run `configure_pzem_address.py` or change an address until you know the meter's current responding ID and are testing one isolated meter.

## Part F — Resume the normal web readings

29. Exit `pzem_multi_reader.py` fully. Confirm no test reader remains by returning to the shell prompt.
30. Reconnect the normal installation only when the wiring is safe and secure. If your installation uses a shared bus, use only a topology and transceiver arrangement supported by the exact PZEM model; do not combine TTL TX lines by assumption.
31. Start the continuous reader again from the project directory:

    ```bash
    python3 main.py
    ```

32. Confirm the terminal prints `Sensor readings:` repeatedly. Record which slave IDs have values and which contain errors.
33. In the web dashboard, check that each working sensor's timestamp advances. `STALE` or `--` means the page has no sufficiently recent saved reading for that channel; it is not a new successful read.
34. If the terminal shows readings but the dashboard timestamp does not advance, check the `Telemetry upload failed:` messages and confirm the Pi's `API_BASE_URL` points to the server's current reachable IP and port.

## What to send back for troubleshooting

Send these items:

1. The exact PZEM model printed on the meter/module.
2. The adapter device name, such as `/dev/ttyUSB0`.
3. For each physical meter tested alone, which of IDs 1/2/3 returned data.
4. The exact error text for each ID that timed out.
5. Whether the meter's readings/timestamp updated on the Pi or in the web dashboard.
