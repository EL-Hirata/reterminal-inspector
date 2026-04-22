from __future__ import annotations

import threading
from collections.abc import Callable

from evdev import InputDevice, categorize, ecodes, list_devices


def find_gpio_keys_device() -> str:
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.name == "gpio_keys":
                return path
        except Exception:
            continue
    raise RuntimeError("gpio_keys device not found")


class SpecialButtonMonitor:
    def __init__(
        self,
        event_path: str | None,
        on_key_press: Callable[[str], None],
        on_key_release: Callable[[str], None],
        on_sleep_press: Callable[[], None],
        on_sleep_release: Callable[[], None],
        on_debug: Callable[[str], None] | None = None,
    ) -> None:
        self.event_path = event_path
        self.on_key_press = on_key_press
        self.on_key_release = on_key_release
        self.on_sleep_press = on_sleep_press
        self.on_sleep_release = on_sleep_release
        self.on_debug = on_debug
        self._running = False
        self._thread: threading.Thread | None = None

        self._code_to_key = {
            ecodes.KEY_A: "a",
            ecodes.KEY_S: "s",
            ecodes.KEY_D: "d",
            ecodes.KEY_F: "f",
        }

    def _debug(self, message: str) -> None:
        if self.on_debug is not None:
            self.on_debug(message)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._debug(f"SpecialButtonMonitor start: {self.event_path or 'auto'}")

    def stop(self) -> None:
        self._running = False
        self._debug("SpecialButtonMonitor stop")

    def _worker(self) -> None:
        self._debug("worker thread started")
        try:
            path = self.event_path or find_gpio_keys_device()
            self._debug(f"trying open: {path}")
            dev = InputDevice(path)
            self._debug(f"Opened input device: {dev.path} / {dev.name}")
        except Exception as exc:
            self._debug(f"Failed to open input device: {self.event_path} / {type(exc).__name__}: {exc}")
            return

        try:
            for event in dev.read_loop():
                if not self._running:
                    break

                if event.type != ecodes.EV_KEY:
                    continue

                key_event = categorize(event)
                scancode = key_event.scancode
                keystate = key_event.keystate

                self._debug(f"EV_KEY: scancode={scancode}, keystate={keystate}")

                if scancode == ecodes.KEY_SLEEP:
                    if keystate == key_event.key_down:
                        self.on_sleep_press()
                    elif keystate == key_event.key_up:
                        self.on_sleep_release()
                    continue

                if scancode not in self._code_to_key:
                    continue

                key_name = self._code_to_key[scancode]

                if keystate == key_event.key_down:
                    self.on_key_press(key_name)
                elif keystate == key_event.key_up:
                    self.on_key_release(key_name)
        except Exception as exc:
            self._debug(f"read_loop error: {type(exc).__name__}: {exc}")