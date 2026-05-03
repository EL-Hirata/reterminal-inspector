from __future__ import annotations

import subprocess
from pathlib import Path


class ReTerminalLeds:
    def __init__(self) -> None:
        self.led_paths = {
            "usr_led0": Path("/sys/class/leds/usr_led0/brightness"),
            "usr_led1": Path("/sys/class/leds/usr_led1/brightness"),
            "usr_led2": Path("/sys/class/leds/usr_led2/brightness"),
        }

    def is_available(self) -> bool:
        return all(path.exists() for path in self.led_paths.values())

    def _write_value(self, path: Path, value: int) -> None:
        cmd = ["sudo", "-n", "tee", str(path)]
        result = subprocess.run(
            cmd,
            input=str(value),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "LED write failed")

    def set_led(self, led_name: str, brightness: int) -> None:
        if led_name not in self.led_paths:
            raise ValueError(f"unknown led: {led_name}")

        value = max(0, min(255, int(brightness)))
        self._write_value(self.led_paths[led_name], value)

    def off_all(self) -> None:
        for path in self.led_paths.values():
            self._write_value(path, 0)

    def set_only(self, led_name: str, brightness: int = 255) -> None:
        for name, path in self.led_paths.items():
            self._write_value(path, brightness if name == led_name else 0)
