"""Runtime RFID reader and local allow-list for authorized reset cards."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

RFID_RST_GPIO = int(os.environ.get("RFID_RST_GPIO", "25"))

try:
    from mfrc522 import MFRC522, SimpleMFRC522
except ModuleNotFoundError:
    MFRC522 = None
    SimpleMFRC522 = None

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    GPIO = None


def _new_reader():
    """Build the standard reader with RST on a GPIO not used by the relays."""
    if MFRC522 is None or SimpleMFRC522 is None:
        raise RuntimeError("mfrc522 library is not installed")

    class ConfiguredSimpleMFRC522(SimpleMFRC522):
        def __init__(self):
            self.READER = MFRC522(pin_rst=RFID_RST_GPIO)

    return ConfiguredSimpleMFRC522()


class _SimulatedRFIDReader:
    """Return one configured card scan in explicit simulation mode only."""

    def __init__(self):
        self._reported = False

    def read(self):
        card_id = int(os.environ.get("SIMULATED_RFID_ID", "1234567890"))
        print("SIMULATION ONLY: returning configured simulated RFID ID")
        return card_id, "simulation"

    def read_id_no_block(self):
        if self._reported:
            return None
        self._reported = True
        card_id = int(os.environ.get("SIMULATED_RFID_ID", "1234567890"))
        print("SIMULATION ONLY: returning one configured simulated RFID scan")
        return card_id


def _authorized_ids_from_environment():
    raw_ids = os.environ.get("RFID_RESET_IDS", os.environ.get("AUTHORIZED_RFID_IDS", ""))
    ids = set()
    for value in raw_ids.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            card_id = int(value)
        except ValueError:
            print(f"Ignoring invalid RFID_RESET_IDS entry: {value!r}")
            continue
        if card_id > 0:
            ids.add(card_id)
    return ids


# Configure authorized reset cards in the Pi's untracked .env file.
AUTHORIZED_IDS = _authorized_ids_from_environment()
RFID_RESET_TIMEOUT_SECONDS = 5.0
reader = None

__all__ = [
    "AUTHORIZED_IDS",
    "RFID_RESET_TIMEOUT_SECONDS",
    "check_user",
    "init_reader",
    "is_authorized",
    "read_rfid_id",
    "read_rfid_id_no_block",
]


def init_reader():
    """Initialize the MFRC522 lazily after the device process starts."""
    global reader
    if reader is not None:
        return True
    if os.environ.get("SIMULATE_HARDWARE") == "1":
        reader = _SimulatedRFIDReader()
        return True
    if SimpleMFRC522 is None:
        print("RFID library unavailable; RFID reset is disabled.")
        return False
    if GPIO is None:
        print("RPi.GPIO unavailable; RFID reset is disabled.")
        return False
    try:
        current_mode = GPIO.getmode()
        if current_mode is None:
            GPIO.setmode(GPIO.BCM)
        elif current_mode != GPIO.BCM:
            raise RuntimeError("GPIO is already configured for BOARD numbering; RFID_RST_GPIO uses BCM numbering")
        reader = _new_reader()
        return True
    except Exception as exc:
        print(f"RFID initialization failed; RFID reset is disabled: {exc}")
        reader = None
        return False


def read_rfid_id():
    """Blocking card read for the standalone manual interface."""
    try:
        if reader is None and not init_reader():
            return None
        card_id, _text = reader.read()
        return int(card_id)
    except Exception as exc:
        print(f"RFID read error: {exc}")
        return None


def read_rfid_id_no_block():
    """Read a card without blocking the sensor/control loop."""
    try:
        if reader is None and not init_reader():
            return None
        scan = getattr(reader, "read_id_no_block", None)
        if not callable(scan):
            return None
        card_id = scan()
        return int(card_id) if card_id is not None else None
    except Exception as exc:
        print(f"RFID read error: {exc}")
        return None


def is_authorized(card_id):
    try:
        return int(card_id) in AUTHORIZED_IDS
    except (TypeError, ValueError):
        return False


def check_user():
    """Read a card and return whether it is in the configured allow-list."""
    card_id = read_rfid_id()
    if card_id is None:
        return False
    if is_authorized(card_id):
        print("RFID access granted.")
        return True
    print("RFID access denied.")
    return False
