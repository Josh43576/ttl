# PZEM-004T V4 setup for the Raspberry Pi reader

## USB-to-TTL port and meter mapping

This installation uses a separate USB-to-TTL adapter for each PZEM. The reader is configured as follows:

| PZEM slave ID | Raspberry Pi serial port |
| ---: | --- |
| 1 | `/dev/ttyUSB1` |
| 2 | `/dev/ttyUSB0` |
| 3 | `/dev/ttyUSB2` |

The Pi polls each meter through its assigned port. Linux may assign different `ttyUSB` numbers after adapters are unplugged or reconnected; check `ls -l /dev/ttyUSB*` and update the mapping in `sensors/pzem.py` and `simple_rpi3_hub/hub.py` if the assignment changes. The serial settings are 9600 baud, 8 data bits, no parity, and 1 stop bit.

## Test the meters

Stop `main.py` before opening the serial adapters with the test tool. From the project directory, run:

```bash
python3 pzem_multi_reader.py
```

Choose a slave ID to test its configured port, or choose `A` to test all three. The tool should report the mapping before polling. A missing `/dev/ttyUSBx` error means the adapter is not currently detected at that path; a Modbus timeout means no valid reply came from that address on the selected adapter.

## Change an address only when needed

Address changes are not required when a meter already responds at its intended ID. If changing one, stop `main.py`, ensure the selected adapter's data lines connect to only the target meter, and supply the meter's known current ID and desired new ID. For example, change the meter on `/dev/ttyUSB1` from ID 3 to ID 1 with:

```bash
python3 configure_pzem_address.py --port /dev/ttyUSB1 --current-id 3 --new-id 1
```

Confirm the prompt only when that adapter is connected to the intended single meter. The script verifies the new address after writing it. Do not use the same value for `--current-id` and `--new-id`.

## Safety

PZEM modules may be connected to mains voltage. De-energize the equipment before changing wiring, follow the exact meter and adapter manuals, and have a qualified person handle mains-side work. Do not assume multiple TTL TX lines can share one connection.

