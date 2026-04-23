from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    window_title: str = "reTerminal Inspector"
    window_size: str = "1280x720"

    ble_device_name: str = "WioTerminal-GUI"
    ble_service_uuid: str = "12345678-1234-1234-1234-1234567890ab"
    ble_write_char_uuid: str = "12345678-1234-1234-1234-1234567890ac"   # reTerminal -> Wio
    ble_notify_char_uuid: str = "12345678-1234-1234-1234-1234567890ad"  # Wio -> reTerminal
    ble_scan_timeout_sec: float = 5.0