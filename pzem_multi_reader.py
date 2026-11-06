#!/usr/bin/env python3
"""Interactively test each PZEM on its dedicated USB-to-TTL adapter."""
from sensors.pzem import PZEM_PORT_BY_SLAVE_ID, PZEM_SLAVE_IDS, read_pzem

PZEM_IDS = list(PZEM_SLAVE_IDS)


def read_pzem_module(slave_id, port=None):
    if port is None:
        try:
            port = PZEM_PORT_BY_SLAVE_ID[slave_id]
        except KeyError as exc:
            raise ValueError(f"No serial port configured for slave ID {slave_id}") from exc
    return read_pzem(port, slave_id=slave_id)


def print_module_data(data):
    print(f"\n--- PZEM Slave ID {data.get('slave_id', '?')} ---")
    if data.get("error"):
        print(f"ERROR: {data['error']}")
    for key, unit in (("voltage", "V"), ("current", "A"), ("power", "W"), ("energy", "Wh")):
        value = data.get(key)
        print(f"{key.title()}: {value if value is not None else 'unavailable'} {unit}")


def main():
    print("Configured PZEM USB-TTL mapping:")
    for slave_id in PZEM_IDS:
        print(f"  Slave {slave_id} -> {PZEM_PORT_BY_SLAVE_ID[slave_id]}")

    while True:
        raw_choice = input("Select slave ID (1, 2, 3), or A to test all: ").strip().lower()
        if raw_choice in {"a", "all"}:
            selected_slaves = PZEM_IDS
        else:
            try:
                selected_slave = int(raw_choice)
            except ValueError:
                print("Invalid selection. Enter 1, 2, 3, or A.")
                continue
            if selected_slave not in PZEM_IDS:
                print(f"Invalid selection. Choose one of: {', '.join(map(str, PZEM_IDS))}, or A.")
                continue
            selected_slaves = [selected_slave]

        for slave_id in selected_slaves:
            port = PZEM_PORT_BY_SLAVE_ID[slave_id]
            print(f"\nReading slave ID {slave_id} on {port}...")
            print_module_data(read_pzem_module(slave_id, port=port))

        again = input("Test another meter? [y/N]: ").strip().lower()
        if again not in {"y", "yes"}:
            print("Stopping PZEM adapter test.")
            break
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping PZEM reader.")
