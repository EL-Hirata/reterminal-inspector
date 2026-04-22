from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bleak import BleakClient, BleakScanner


@dataclass(slots=True)
class ScanResult:
    name: str
    address: str


class M5BleClient:
    def __init__(
        self,
        device_name: str,
        notify_char_uuid: str,
        write_char_uuid: str,
        scan_timeout_sec: float = 5.0,
    ) -> None:
        self.device_name = device_name
        self.notify_char_uuid = notify_char_uuid
        self.write_char_uuid = write_char_uuid
        self.scan_timeout_sec = scan_timeout_sec
        self.client: BleakClient | None = None

    async def scan(self) -> list[ScanResult]:
        devices = await BleakScanner.discover(timeout=self.scan_timeout_sec)
        results: list[ScanResult] = []

        for dev in devices:
            name = dev.name or ""
            address = getattr(dev, "address", "")
            results.append(ScanResult(name=name, address=address))

        return results

    async def connect(self) -> bool:
        devices = await BleakScanner.discover(timeout=self.scan_timeout_sec)
        target = next((d for d in devices if (d.name or "") == self.device_name), None)
        if target is None:
            return False

        self.client = BleakClient(target)
        await self.client.connect()
        return bool(self.client.is_connected)

    async def disconnect(self) -> None:
        if self.client is not None and self.client.is_connected:
            await self.client.disconnect()

    async def start_notify(self, callback) -> None:
        if self.client is None or not self.client.is_connected:
            raise RuntimeError("BLE 未接続です")
        await self.client.start_notify(self.notify_char_uuid, callback)

    async def stop_notify(self) -> None:
        if self.client is None or not self.client.is_connected:
            return
        try:
            await self.client.stop_notify(self.notify_char_uuid)
        except Exception:
            pass

    async def send_text(self, text: str) -> None:
        if self.client is None or not self.client.is_connected:
            raise RuntimeError("BLE 未接続です")
        await self.client.write_gatt_char(self.write_char_uuid, text.encode("utf-8"))

    @property
    def is_connected(self) -> bool:
        return bool(self.client is not None and self.client.is_connected)