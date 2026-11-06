import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ModuleNotFoundError:
    HARDWARE_AVAILABLE = False

class _GPIO:
    BOARD = "BOARD"
    BCM = "BCM"
    OUT = "OUT"
    HIGH = 1
    LOW = 0
    states = {}

    @staticmethod
    def setwarnings(value):
        pass

    @staticmethod
    def setmode(mode):
        pass

    @staticmethod
    def setup(pin, mode, initial=None):
        if initial is not None:
            _GPIO.states[pin] = initial

    @staticmethod
    def output(pin, value):
        _GPIO.states[pin] = value

    @staticmethod
    def cleanup(*pins):
        pass


if not HARDWARE_AVAILABLE or os.environ.get("SIMULATE_HARDWARE") == "1":
    GPIO = _GPIO()

if os.environ.get("SIMULATE_HARDWARE") == "1":
    HARDWARE_AVAILABLE = False

# Raspberry Pi GPIO mapping for the SSR outputs.
# Physical header pins: 11 = GPIO17, 13 = GPIO27, 15 = GPIO22
# The code uses BCM numbering internally, but the physical wiring matches these pins.
GPIO_RELAY_PINS = [17, 27, 22]
PHYSICAL_RELAY_PINS = [11, 13, 15]
relay_pins = GPIO_RELAY_PINS.copy()
SSR_ACTIVE_HIGH = os.environ.get("SSR_ACTIVE_HIGH", "1").strip().lower() not in {"0", "false", "no", "off"}


def relay_output_level(is_on):
    """Map logical ON/OFF to the configured electrical level at the SSR input."""
    active_level = GPIO.HIGH if SSR_ACTIVE_HIGH else GPIO.LOW
    inactive_level = GPIO.LOW if SSR_ACTIVE_HIGH else GPIO.HIGH
    return active_level if is_on else inactive_level

# Runtime initialization flag
_relays_initialized = False


def init(pins=None):
    """Initialize relay GPIOs at runtime. Call once on startup."""
    global _relays_initialized, relay_pins
    if pins is not None:
        relay_pins = pins

    try:
        if not HARDWARE_AVAILABLE and os.environ.get("SIMULATE_HARDWARE") != "1":
            print("GPIO unavailable. Set SIMULATE_HARDWARE=1 only for an explicit simulation.")
            _relays_initialized = False
            return False
        setwarnings = getattr(GPIO, "setwarnings", None)
        if callable(setwarnings):
            setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for pin in relay_pins:
            GPIO.setup(pin, GPIO.OUT, initial=relay_output_level(False))
            GPIO.output(pin, relay_output_level(False))
        _relays_initialized = True
        return True
    except Exception as e:
        print(f"Relay init failed: {e}")
        for pin in relay_pins:
            try:
                GPIO.output(pin, relay_output_level(False))
            except Exception:
                pass
        _relays_initialized = False
        return False


__all__ = [
    "GPIO_RELAY_PINS", "PHYSICAL_RELAY_PINS", "SSR_ACTIVE_HIGH", "relay_pins",
    "relay_output_level", "control_appliance", "cleanup", "init",
]


def control_appliance(index, state: bool):
    try:
        if not _relays_initialized:
            if not init():
                return False

        if index < 0 or index >= len(relay_pins):
            print(f"Invalid appliance index: {index}")
            return False

        if state:
            GPIO.output(relay_pins[index], relay_output_level(True))
            return True

        GPIO.output(relay_pins[index], relay_output_level(False))
        return True
    except Exception as e:
        print(f"Error controlling appliance {index}: {e}")
        return False


def cleanup():
    try:
        for pin in relay_pins:
            try:
                GPIO.output(pin, relay_output_level(False))
            except Exception:
                pass
        GPIO.cleanup(relay_pins)
    except TypeError:
        GPIO.cleanup()
    finally:
        global _relays_initialized
        _relays_initialized = False
