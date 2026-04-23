from __future__ import annotations

from collections.abc import Callable

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice


class M5BleClient:
    def __init__(
        self,
        device_name: str,
        notify_char_uuid: str,
        write_char_uuid: str,
        scan_timeout_sec: float = 5.0,
        service_uuid: str | None = None,
        debug_log: Callable[[str], None] | None = None,
    ) -> None:
        self.device_name = device_name
        self.notify_char_uuid = notify_char_uuid.lower()
        self.write_char_uuid = write_char_uuid.lower()
        self.scan_timeout_sec = scan_timeout_sec
        self.service_uuid = service_uuid.lower() if service_uuid else None
        self.debug_log = debug_log

        self.device: BLEDevice | None = None
        self.client: BleakClient | None = None

    def _log(self, message: str) -> None:
        if self.debug_log is not None:
            self.debug_log(message)

    async def scan(self) -> list[BLEDevice]:
        self._log(f"[BLE] scan start timeout={self.scan_timeout_sec}")
        devices = await BleakScanner.discover(timeout=self.scan_timeout_sec)
        for dev in devices:
            self._log(
                f"[BLE] scan found name={dev.name!r} address={dev.address}"
            )
        self._log(f"[BLE] scan done count={len(devices)}")
        return list(devices)

    async def _find_device(self) -> BLEDevice | None:
        self._log("[BLE] _find_device: phase1 name scan")
        devices = await BleakScanner.discover(timeout=self.scan_timeout_sec)
        for dev in devices:
            self._log(
                f"[BLE] phase1 candidate name={dev.name!r} address={dev.address}"
            )
            if (dev.name or "") == self.device_name:
                self._log(
                    f"[BLE] phase1 match by name name={dev.name!r} address={dev.address}"
                )
                return dev

        self._log("[BLE] _find_device: phase2 adv callback scan")
        found: BLEDevice | None = None

        def detection_callback(device: BLEDevice, advertisement_data) -> None:
            nonlocal found

            if found is not None:
                return

            name = device.name or advertisement_data.local_name or ""
            service_uuids = [u.lower() for u in (advertisement_data.service_uuids or [])]

            self._log(
                f"[BLE] adv name={name!r} address={device.address} uuids={service_uuids}"
            )

            if name == self.device_name:
                found = device
                self._log(
                    f"[BLE] phase2 match by name name={name!r} address={device.address}"
                )
                return

            if self.service_uuid and self.service_uuid in service_uuids:
                found = device
                self._log(
                    f"[BLE] phase2 match by uuid uuid={self.service_uuid} address={device.address}"
                )
                return

        scanner = BleakScanner(detection_callback=detection_callback)

        try:
            await scanner.start()
            await scanner.discover(timeout=self.scan_timeout_sec)
        finally:
            await scanner.stop()

        if found is None:
            self._log("[BLE] _find_device: no match")
        return found

    async def connect(self) -> bool:
        self._log("[BLE] connect begin")
        self.device = await self._find_device()
        if self.device is None:
            self._log("[BLE] connect abort: device not found")
            return False

        self._log(
            f"[BLE] connecting to name={self.device.name!r} address={self.device.address}"
        )
        self.client = BleakClient(self.device)
        await self.client.connect()
        connected = bool(self.client.is_connected)
        self._log(f"[BLE] connect result connected={connected}")

        if connected and self.client is not None:
            try:
                services = await self.client.get_services()
                self._log("[BLE] service discovery done")
                for service in services:
                    self._log(f"[BLE] service uuid={service.uuid}")
                    for char in service.characteristics:
                        props = ",".join(char.properties)
                        self._log(
                            f"[BLE]   char uuid={char.uuid.lower()} props=[{props}]"
                        )
            except Exception as exc:
                self._log(
                    f"[BLE] service discovery failed: {type(exc).__name__}: {exc}"
                )

        return connected

    async def disconnect(self) -> None:
        if self.client is not None:
            self._log("[BLE] disconnect begin")
            await self.client.disconnect()
            self._log("[BLE] disconnect done")
            self.client = None

    async def start_notify(self, callback: Callable[[int, bytearray], None]) -> None:
        if self.client is None:
            raise RuntimeError("BLE client is not connected")
        self._log(f"[BLE] start_notify uuid={self.notify_char_uuid}")
        await self.client.start_notify(self.notify_char_uuid, callback)
        self._log("[BLE] start_notify ok")

    async def stop_notify(self) -> None:
        if self.client is None:
            return
        try:
            self._log(f"[BLE] stop_notify uuid={self.notify_char_uuid}")
            await self.client.stop_notify(self.notify_char_uuid)
            self._log("[BLE] stop_notify ok")
        except Exception as exc:
            self._log(f"[BLE] stop_notify ignored: {type(exc).__name__}: {exc}")

    async def send_text(self, text: str) -> None:
        if self.client is None:
            raise RuntimeError("BLE client is not connected")
        self._log(f"[BLE] write uuid={self.write_char_uuid} text={text!r}")
        await self.client.write_gatt_char(self.write_char_uuid, text.encode("utf-8"))
        self._log("[BLE] write ok")