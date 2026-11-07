"""Authenticated HTTP client for the Raspberry Pi device agent."""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load the same project-level settings when launched directly on the Pi.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_PRESET_LIMIT = 500.0
DEFAULT_APPLIANCE_NAMES = ["Appliance 1", "Appliance 2", "Appliance 3"]
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
DEVICE_API_TOKEN = os.environ.get("DEVICE_API_TOKEN", "")
try:
    REQUEST_TIMEOUT = max(0.1, float(os.environ.get("API_TIMEOUT_SECONDS", "5")))
except ValueError:
    REQUEST_TIMEOUT = 5.0


def _headers():
    if not DEVICE_API_TOKEN:
        raise RuntimeError("DEVICE_API_TOKEN is required for device API requests")
    return {"Authorization": f"Bearer {DEVICE_API_TOKEN}"}


def send_to_server(data):
    response = requests.post(
        f"{API_BASE_URL}/api/data", json=data, headers=_headers(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def reset_tripped_appliances():
    """Apply the confirmed RFID reset and return any local meter-budget resets."""
    response = requests.post(
        f"{API_BASE_URL}/api/rfid-reset", json={}, headers=_headers(), timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def notify_kiosk_event(action):
    """Update the admin kiosk screen after a locally validated RFID scan."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/kiosk/event", json={"action": action},
            headers=_headers(), timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Kiosk status upload failed: {exc}")
        return False


def ack_energy_resets(slave_ids):
    """Acknowledge local daily-budget resets after the Pi has persisted them."""
    if not slave_ids:
        return True
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/energy-reset-ack", json={"slave_ids": list(slave_ids)},
            headers=_headers(), timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Energy reset acknowledgement failed: {exc}")
        return False


def get_control_commands(silent=False):
    """Read persisted relay requests. Return connected=False on any API failure."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/control", headers=_headers(), timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
        states = payload.get("appliances") if isinstance(payload, dict) else None
        tripped = payload.get("tripped") if isinstance(payload, dict) else None
        if (
            not isinstance(states, list) or len(states) != 3
            or any(s not in ("ON", "OFF") for s in states)
            or not isinstance(tripped, list) or len(tripped) != 3
            or any(type(value) is not bool for value in tripped)
        ):
            raise ValueError("invalid control response")
        payload["connected"] = True
        payload.setdefault("preset_limit", DEFAULT_PRESET_LIMIT)
        payload.setdefault("appliance_names", DEFAULT_APPLIANCE_NAMES)
        return payload
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        if not silent:
            print(f"Control API unavailable: {exc}")
        return {"appliances": ["OFF"] * 3, "connected": False,
                "tripped": [True] * 3,
                "energy_reset_slaves": [],
                "preset_limit": DEFAULT_PRESET_LIMIT,
                "appliance_names": DEFAULT_APPLIANCE_NAMES}


def get_appliance_configs():
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/appliance-config", headers=_headers(), timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
        configs = payload.get("configs") if isinstance(payload, dict) else None
        if isinstance(configs, dict):
            return configs
        raise ValueError("invalid appliance-config response")
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print(f"Appliance config API unavailable: {exc}")
        return None


def report_trip(index, value, limit, reason="power_limit", unit="W"):
    measurements = ({"value_wh": value, "limit_wh": limit} if unit == "Wh"
                    else {"value_watts": value, "limit_watts": limit})
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/device-trip",
            json={"index": index, **measurements, "unit": unit, "reason": reason},
            headers=_headers(), timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Trip-state upload failed: {exc}")
        return False


def set_appliance_names(names):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/config", json={"appliance_names": names},
            headers=_headers(), timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Error setting appliance names: {exc}")
        return {"error": str(exc)}
