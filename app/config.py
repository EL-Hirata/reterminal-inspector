from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppConfig:
    window_title: str = "reTerminal 検査装置"
    window_size: str = "1280x720"

    ble_device_name: str = "WIO-SCPI"
    ble_service_uuid: str = "12345678-1234-1234-1234-1234567890ab"
    ble_notify_char_uuid: str = "12345678-1234-1234-1234-1234567890ac"
    ble_write_char_uuid: str = "12345678-1234-1234-1234-1234567890ad"
    ble_scan_timeout_sec: float = 5.0