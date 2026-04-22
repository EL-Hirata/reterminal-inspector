from __future__ import annotations

import asyncio
import subprocess
import threading
import time

from app.ble_client import M5BleClient
from app.config import AppConfig
from app.leds import ReTerminalLeds
from app.special_buttons import SpecialButtonMonitor


class AppController:
    def __init__(self, config: AppConfig, gui) -> None:
        self.config = config
        self.gui = gui

        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.loop_thread.start()

        self.ble = M5BleClient(
            device_name=self.config.ble_device_name,
            notify_char_uuid=self.config.ble_notify_char_uuid,
            write_char_uuid=self.config.ble_write_char_uuid,
            scan_timeout_sec=self.config.ble_scan_timeout_sec,
        )

        self.leds = ReTerminalLeds()
        self.led_ready = False
        self.ble_connected = False
        self.rx_indicator_job: str | None = None

        self.button_states: dict[str, bool] = {
            "F1": False,
            "F2": False,
            "F3": False,
            "○": False,
        }
        self.key_to_button = {
            "a": "F1",
            "s": "F2",
            "d": "F3",
            "f": "○",
        }

        self.f_press_time: float | None = None
        self.f_long_press_triggered = False
        self.f_long_press_ms = 3000

        self.special_monitor = SpecialButtonMonitor(
            event_path=None,
            on_key_press=self._on_gpio_key_press_threadsafe,
            on_key_release=self._on_gpio_key_release_threadsafe,
            on_sleep_press=self._noop_sleep_press,
            on_sleep_release=self._noop_sleep_release,
            on_debug=lambda msg: self.gui.root.after(0, lambda: self.gui.append_log(f"[GPIO] {msg}")),
        )

    def start(self) -> None:
        self._init_leds()
        self._refresh_button_indicators()
        self.special_monitor.start()
        self.gui.append_log("アプリ起動")
        self.gui.append_log("キー入力待機: a / s / d / f")
        self.gui.append_log("上部ボタン機能は無効")
        self.gui.append_log("○短押し=BLE接続 / ○長押し3秒=シャットダウン確認")
        self._update_ble_status_led()

    def stop(self) -> None:
        async def _cleanup_ble() -> None:
            try:
                await self.ble.stop_notify()
            except Exception:
                pass
            try:
                await self.ble.disconnect()
            except Exception:
                pass

        try:
            future = asyncio.run_coroutine_threadsafe(_cleanup_ble(), self.loop)
            future.result(timeout=2)
        except Exception:
            pass

        try:
            self.special_monitor.stop()
        except Exception:
            pass

        try:
            if self.led_ready:
                self.leds.off_all()
        except Exception:
            pass

        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _submit_coro(self, coro) -> None:
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _safe_ui(self, func) -> None:
        self.gui.root.after(0, func)

    def _noop_sleep_press(self) -> None:
        pass

    def _noop_sleep_release(self) -> None:
        pass

    def _init_leds(self) -> None:
        try:
            if not self.leds.is_available():
                self.gui.set_led_text("LED: デバイス未検出")
                return
            self.leds.off_all()
            self.led_ready = True
            self.gui.set_led_text("LED: 利用可能")
        except Exception as exc:
            self.gui.set_led_text(f"LED: 使用不可 ({exc})")

    def _update_ble_status_led(self) -> None:
        if not self.led_ready:
            self.gui.set_led_text("LED: 使用不可")
            return

        try:
            self.leds.off_all()
            if self.ble_connected:
                self.leds.set_led("usr_led1", 0)
                self.leds.set_led("usr_led2", 255)
                self.gui.set_led_text("LED: BLE接続(緑)")
            else:
                self.leds.set_led("usr_led2", 0)
                self.leds.set_led("usr_led1", 255)
                self.gui.set_led_text("LED: BLE未接続(赤)")
        except Exception as exc:
            self.gui.set_led_text(f"LEDエラー: {exc}")
            self.gui.append_log(f"LEDエラー: {exc}")

    def _pulse_rx_led(self) -> None:
        if not self.led_ready:
            return

        try:
            self.leds.set_led("usr_led0", 255)
        except Exception as exc:
            self.gui.append_log(f"RX LEDエラー: {exc}")
            return

        if self.rx_indicator_job is not None:
            try:
                self.gui.root.after_cancel(self.rx_indicator_job)
            except Exception:
                pass

        self.rx_indicator_job = self.gui.root.after(120, self._turn_off_rx_led)

    def _turn_off_rx_led(self) -> None:
        self.rx_indicator_job = None
        if not self.led_ready:
            return
        try:
            self.leds.set_led("usr_led0", 0)
        except Exception as exc:
            self.gui.append_log(f"RX LEDエラー: {exc}")

    def turn_off_leds(self) -> None:
        if not self.led_ready:
            self.gui.set_led_text("LED: 使用不可")
            return

        try:
            self.leds.off_all()
            self.gui.set_led_text("LED: 全消灯")
            self.gui.append_log("LED 全消灯")
        except Exception as exc:
            self.gui.set_led_text(f"LEDエラー: {exc}")
            self.gui.append_log(f"LEDエラー: {exc}")

    def _on_gpio_key_press_threadsafe(self, key_name: str) -> None:
        self.gui.root.after(0, lambda: self._on_key_press(key_name))

    def _on_gpio_key_release_threadsafe(self, key_name: str) -> None:
        self.gui.root.after(0, lambda: self._on_key_release(key_name))

    def _make_wio_btn_payload(self) -> str:
        a = 1 if self.button_states["F1"] else 0
        b = 1 if self.button_states["F2"] else 0
        c = 1 if self.button_states["F3"] else 0
        return f"M5:BTN {a},{b},{c}"

    def _send_wio_button_state(self) -> None:
        if not self.ble_connected:
            return

        payload = self._make_wio_btn_payload()

        async def _task() -> None:
            try:
                await self.ble.send_text(payload)
                self._safe_ui(lambda: self.gui.append_log(f"送信: {payload}"))
            except Exception as exc:
                self._safe_ui(lambda: self.gui.append_log(f"送信失敗: {exc}"))

        self._submit_coro(_task())

    def _on_key_press(self, key_name: str) -> None:
        button_name = self.key_to_button[key_name]

        if self.button_states[button_name]:
            return

        self.button_states[button_name] = True
        self._refresh_button_indicators()

        text = f"{button_name} 押下 (key={key_name})"
        self.gui.set_button_text(text)
        self.gui.set_status("物理ボタン入力")
        self.gui.append_log(text)

        if button_name == "○":
            self.f_press_time = time.monotonic()
            self.f_long_press_triggered = False
            self.gui.root.after(100, self._check_f_long_press)
            return

        self._send_wio_button_state()

    def _on_key_release(self, key_name: str) -> None:
        button_name = self.key_to_button[key_name]

        if not self.button_states[button_name]:
            return

        self.button_states[button_name] = False
        self._refresh_button_indicators()

        self.gui.set_button_text(f"{button_name} 離上")
        self.gui.set_status("待機中")
        self.gui.append_log(f"{button_name} 離上 (key={key_name})")

        if button_name == "○":
            was_long = self.f_long_press_triggered
            self.f_press_time = None
            if not was_long:
                self.connect_ble()
            return

        self._send_wio_button_state()

    def _check_f_long_press(self) -> None:
        if self.f_press_time is None:
            return

        if self.f_long_press_triggered:
            return

        elapsed_ms = (time.monotonic() - self.f_press_time) * 1000
        if elapsed_ms >= self.f_long_press_ms:
            self.f_long_press_triggered = True
            self.gui.set_button_text("○ 長押し")
            self.gui.append_log("○ 長押し検出")
            self._show_shutdown_dialog()
        else:
            self.gui.root.after(100, self._check_f_long_press)

    def _refresh_button_indicators(self) -> None:
        for button_name, is_on in self.button_states.items():
            self.gui.set_indicator(button_name, is_on)

    def _show_shutdown_dialog(self) -> None:
        result = self.gui.ask_shutdown_dialog()

        if result:
            self.gui.append_log("シャットダウン実行")
            self._shutdown_system()
        else:
            self.gui.append_log("シャットダウン取消")
            self.gui.set_button_text("○ 長押し取消")

    def _shutdown_system(self) -> None:
        try:
            subprocess.Popen(
                ["sudo", "-n", "systemctl", "poweroff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            self.gui.append_log(f"シャットダウン失敗: {exc}")
            self.gui.set_button_text("シャットダウン失敗")

    def scan_ble(self) -> None:
        async def _task() -> None:
            try:
                results = await self.ble.scan()
                lines = [f"{r.name or '(no name)'} / {r.address}" for r in results]
                if not lines:
                    self._safe_ui(lambda: self.gui.append_log("BLE scan: デバイスなし"))
                    self._safe_ui(lambda: self.gui.set_status("BLE scan: デバイスなし"))
                    return

                def _update() -> None:
                    self.gui.set_status(f"BLE scan: {len(lines)}件")
                    self.gui.append_log("BLE scan 結果:")
                    for line in lines:
                        self.gui.append_log(f"  {line}")

                self._safe_ui(_update)
            except Exception as exc:
                self._safe_ui(lambda: self.gui.set_status(f"BLE scan 失敗: {exc}"))
                self._safe_ui(lambda: self.gui.append_log(f"BLE scan 失敗: {exc}"))

        self._submit_coro(_task())

    def connect_ble(self) -> None:
        if self.ble_connected:
            self.gui.append_log("BLE は既に接続中")
            self.gui.set_status("BLE接続中")
            return

        async def _task() -> None:
            try:
                ok = await self.ble.connect()
                if not ok:
                    self._safe_ui(lambda: self.gui.set_ble_text("BLE: 対象未検出"))
                    self._safe_ui(lambda: self.gui.set_status("BLE接続失敗"))
                    self._safe_ui(lambda: self.gui.append_log(f"{self.config.ble_device_name} が見つかりません"))
                    self._safe_ui(self._update_ble_status_led)
                    return

                await self.ble.start_notify(self._notify_handler)
                await self.ble.send_text("*IDN?")

                self.ble_connected = True

                self._safe_ui(lambda: self.gui.set_ble_text("BLE: 接続中"))
                self._safe_ui(lambda: self.gui.set_status("BLE接続成功"))
                self._safe_ui(lambda: self.gui.append_log("BLE接続成功"))
                self._safe_ui(self._update_ble_status_led)
            except Exception as exc:
                self.ble_connected = False
                self._safe_ui(lambda: self.gui.set_ble_text("BLE: エラー"))
                self._safe_ui(lambda: self.gui.set_status(f"BLE接続失敗: {exc}"))
                self._safe_ui(lambda: self.gui.append_log(f"BLE接続失敗: {exc}"))
                self._safe_ui(self._update_ble_status_led)

        self._submit_coro(_task())

    def disconnect_ble(self) -> None:
        async def _task() -> None:
            try:
                await self.ble.stop_notify()
                await self.ble.disconnect()
                self.ble_connected = False
                self._safe_ui(lambda: self.gui.set_ble_text("BLE: 未接続"))
                self._safe_ui(lambda: self.gui.set_status("BLE切断"))
                self._safe_ui(lambda: self.gui.append_log("BLE切断"))
                self._safe_ui(self._update_ble_status_led)
            except Exception as exc:
                self.ble_connected = False
                self._safe_ui(lambda: self.gui.set_status(f"BLE切断失敗: {exc}"))
                self._safe_ui(lambda: self.gui.append_log(f"BLE切断失敗: {exc}"))
                self._safe_ui(self._update_ble_status_led)

        self._submit_coro(_task())

    def send_idn(self) -> None:
        async def _task() -> None:
            try:
                await self.ble.send_text("*IDN?")
                self._safe_ui(lambda: self.gui.set_status("IDN送信"))
                self._safe_ui(lambda: self.gui.append_log("送信: *IDN?"))
            except Exception as exc:
                self._safe_ui(lambda: self.gui.set_status(f"送信失敗: {exc}"))
                self._safe_ui(lambda: self.gui.append_log(f"送信失敗: {exc}"))

        self._submit_coro(_task())

    def _notify_handler(self, _sender: int, data: bytearray) -> None:
        text = data.decode("utf-8", errors="ignore")

        def _update() -> None:
            self.gui.set_recv_text(text)
            self.gui.set_status("BLE受信")
            self.gui.append_log(f"受信: {text}")
            self._pulse_rx_led()

            if text.startswith("WIO:BTN "):
                self.gui.set_button_text(text)

        self._safe_ui(_update)