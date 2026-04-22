from __future__ import annotations

import asyncio

from bleak import BleakClient, BleakScanner

DEVICE_NAME = "WIO-SCPI"
NOTIFY_UUID = "12345678-1234-1234-1234-1234567890ac"
WRITE_UUID = "12345678-1234-1234-1234-1234567890ad"


def notify_handler(_sender: int, data: bytearray) -> None:
    text = data.decode("utf-8", errors="ignore")
    print("NOTIFY:", text)


async def main() -> None:
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=5.0)
    target = next((d for d in devices if (d.name or "") == DEVICE_NAME), None)

    if target is None:
        print("WIO-SCPI not found")
        return

    print("Found:", target.name, target.address)

    async with BleakClient(target) as client:
        print("Connected:", client.is_connected)

        await client.start_notify(NOTIFY_UUID, notify_handler)

        await client.write_gatt_char(WRITE_UUID, b"*IDN?")
        await asyncio.sleep(0.3)

        print("Waiting for READY / WIO:BTN ...")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())