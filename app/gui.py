from __future__ import annotations

import asyncio
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from app.ble_client import M5BleClient
from app.config import AppConfig
from app.leds import ReTerminalLeds
from app.special_buttons import SpecialButtonMonitor


class MainWindow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

        self.root = tk.Tk()
        self.root.title(self.config.window_title)
        self.root.geometry(self.config.window_size)
        self.root.attributes("-fullscreen", True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure("Big.TButton", font=("", 15, "bold"), padding=(14, 14))
        self.style.configure("Info.TLabel", font=("", 13))
        self.style.configure("Value.TLabel", font=("", 14, "bold"))
        self.style.configure("Title.TLabel", font=("", 22, "bold"))
        self.style.configure("Section.TLabelframe.Label", font=("", 13, "bold"))

        self.status_var = tk.StringVar(value="待機中")
        self.ble_var = tk.StringVar(value="BLE: 未接続")
        self.recv_var = tk.StringVar(value="-")
        self.button_var = tk.StringVar(value="未入力")
        self.keymap_var = tk.StringVar(value="F1=a / F2=s / F3=d / ○=f")
        self.led_var = tk.StringVar(value="LED: 初期化前")
        self.sleep_button_var = tk.StringVar(value="未入力")

        self.sleep_press_time: float | None = None
        self.sleep_long_press_triggered = False
        self.sleep_long_press_ms = 2000

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
        self._init_leds()

        self.button_widgets: dict[str, dict[str, tk.Widget]] = {}
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
        self.button_to_key = {
            "F1": "a",
            "F2": "s",
            "F3": "d",
            "○": "f",
        }
        self.button_to_led = {
            "F1": "usr_led0",
            "F2": "usr_led1",
            "F3": "usr_led2",
            "○": None,
        }

        self.special_monitor = SpecialButtonMonitor(
            event_path=None,
            on_key_press=self._on_gpio_key_press_threadsafe,
            on_key_release=self._on_gpio_key_release_threadsafe,
            on_sleep_press=self._on_sleep_button_press_threadsafe,
            on_sleep_release=self._on_sleep_button_release_threadsafe,
            on_debug=lambda msg: self.root.after(0, lambda: self._append_log(f"[GPIO] {msg}")),
        )

        self._build_ui()
        self._bind_keys()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _init_leds(self) -> None:
        try:
            if not self.leds.is_available():
                self.led_var.set("LED: デバイス未検出")
                return
            self.leds.off_all()
            self.led_ready = True
            self.led_var.set("LED: 利用可能")
        except Exception as exc:
            self.led_var.set(f"LED: 使用不可 ({exc})")

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text=self.config.window_title, style="Title.TLabel")
        title.pack(anchor="w", pady=(0, 4))

        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 6))

        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=4)
        top.rowconfigure(0, weight=1)

        left_top = ttk.Frame(top)
        left_top.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        right_top = ttk.Frame(top)
        right_top.grid(row=0, column=1, sticky="nsew")

        info_frame = ttk.LabelFrame(left_top, text="状態", padding=10, style="Section.TLabelframe")
        info_frame.pack(fill="both", expand=True)

        self._make_info_row(info_frame, "状態", self.status_var, 0)
        self._make_info_row(info_frame, "BLE", self.ble_var, 1)
        self._make_info_row(info_frame, "受信", self.recv_var, 2)
        self._make_info_row(info_frame, "ボタン", self.button_var, 3)
        self._make_info_row(info_frame, "割当", self.keymap_var, 4)
        self._make_info_row(info_frame, "LED", self.led_var, 5)
        self._make_info_row(info_frame, "上部BTN", self.sleep_button_var, 6)

        log_frame = ttk.LabelFrame(right_top, text="ログ", padding=8, style="Section.TLabelframe")
        log_frame.pack(fill="both", expand=True)

        self.log_text = ScrolledText(log_frame, height=12, font=("", 12))
        self.log_text.pack(fill="both", expand=True)

        action_frame = ttk.LabelFrame(main, text="操作", padding=10, style="Section.TLabelframe")
        action_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(action_frame, text="BLEスキャン", command=self.scan_ble, style="Big.TButton").grid(
            row=0, column=0, padx=8, pady=8, sticky="ew"
        )
        ttk.Button(action_frame, text="BLE接続", command=self.connect_ble, style="Big.TButton").grid(
            row=0, column=1, padx=8, pady=8, sticky="ew"
        )
        ttk.Button(action_frame, text="PING送信", command=self.send_ping, style="Big.TButton").grid(
            row=0, column=2, padx=8, pady=8, sticky="ew"
        )
        ttk.Button(action_frame, text="BLE切断", command=self.disconnect_ble, style="Big.TButton").grid(
            row=0, column=3, padx=8, pady=8, sticky="ew"
        )
        ttk.Button(action_frame, text="LED全消灯", command=self.turn_off_leds, style="Big.TButton").grid(
            row=0, column=4, padx=8, pady=8, sticky="ew"
        )
        ttk.Button(action_frame, text="終了", command=self.on_close, style="Big.TButton").grid(
            row=0, column=5, padx=8, pady=8, sticky="ew"
        )

        for col in range(6):
            action_frame.columnconfigure(col, weight=1)

        button_frame = ttk.LabelFrame(main, text="物理ボタン状態", padding=8, style="Section.TLabelframe")
        button_frame.pack(fill="x")

        ttk.Label(
            button_frame,
            text="F1/F2/F3/○ → a/s/d/f",
            font=("", 11, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        indicator_frame = ttk.Frame(button_frame)
        indicator_frame.pack(fill="x")

        self._create_indicator(indicator_frame, 0, "F1", "a")
        self._create_indicator(indicator_frame, 1, "F2", "s")
        self._create_indicator(indicator_frame, 2, "F3", "d")
        self._create_indicator(indicator_frame, 3, "○", "f")

        self.special_monitor.start()

        self._append_log("アプリ起動")
        self._append_log("キー入力待機: a / s / d / f")
        self._append_log("KEY_SLEEP 監視開始")

    def _create_indicator(self, parent: ttk.Frame, column: int, button_name: str, key_name: str) -> None:
        outer = tk.Frame(parent, bd=2, relief="groove", bg="#505050")
        outer.grid(row=0, column=column, padx=6, pady=2, sticky="nsew")
        parent.columnconfigure(column, weight=1)

        title = tk.Label(
            outer,
            text=button_name,
            font=("", 12, "bold"),
            bg="#505050",
            fg="white",
        )
        title.pack(fill="x", padx=2, pady=(2, 1))

        inner = tk.Label(
            outer,
            text=f"{key_name}\nOFF",
            font=("", 12, "bold"),
            width=8,
            height=2,
            bg="#808080",
            fg="white",
            relief="flat",
            bd=0,
        )
        inner.pack(fill="both", expand=True, padx=4, pady=(1, 4))

        self.button_widgets[button_name] = {
            "outer": outer,
            "title": title,
            "inner": inner,
        }

    def _on_gpio_key_press_threadsafe(self, key_name: str) -> None:
        self.root.after(0, lambda: self._on_key_press(key_name))

    def _on_gpio_key_release_threadsafe(self, key_name: str) -> None:
        self.root.after(0, lambda: self._on_key_release(key_name))

    def _bind_keys(self) -> None:
        self.root.bind("<Button-1>", lambda _e: self.root.focus_force())
        self.root.after(300, self.root.focus_force)

    def _on_key_press(self, key_name: str) -> None:
        button_name = self.key_to_button[key_name]

        if self.button_states[button_name]:
            return

        self.button_states[button_name] = True
        self._refresh_button_indicators()
        self._turn_on_led_for_button(button_name)

        text = f"{button_name} 押下 (key={key_name})"
        self.button_var.set(text)
        self.status_var.set("物理ボタン入力")
        self._append_log(text)

    def _on_key_release(self, key_name: str) -> None:
        button_name = self.key_to_button[key_name]

        if not self.button_states[button_name]:
            return

        self.button_states[button_name] = False
        self._refresh_button_indicators()
        self._turn_off_leds()

        self.button_var.set(f"{button_name} 離上")
        self.status_var.set("待機中")
        self._append_log(f"{button_name} 離上 (key={key_name})")

    def _refresh_button_indicators(self) -> None:
        for button_name, widgets in self.button_widgets.items():
            key_name = self.button_to_key[button_name]
            outer = widgets["outer"]
            title = widgets["title"]
            inner = widgets["inner"]

            if self.button_states[button_name]:
                outer.config(bg="#00a844")
                title.config(bg="#00a844", fg="white")
                inner.config(
                    bg="#00c853",
                    fg="white",
                    text=f"{key_name}\nON",
                )
            else:
                outer.config(bg="#505050")
                title.config(bg="#505050", fg="white")
                inner.config(
                    bg="#808080",
                    fg="white",
                    text=f"{key_name}\nOFF",
                )

        self.root.update_idletasks()

    def _turn_on_led_for_button(self, button_name: str) -> None:
        if not self.led_ready:
            self.led_var.set("LED: 使用不可")
            return

        try:
            led_name = self.button_to_led[button_name]
            if led_name is None:
                self.leds.off_all()
                self.led_var.set("LED: OFF")
            else:
                self.leds.set_only(led_name)
                self.led_var.set(f"LED: {led_name} ON")
        except Exception as exc:
            self.led_var.set(f"LEDエラー: {exc}")
            self._append_log(f"LEDエラー: {exc}")

    def _turn_off_leds(self) -> None:
        if not self.led_ready:
            self.led_var.set("LED: 使用不可")
            return

        try:
            self.leds.off_all()
            self.led_var.set("LED: OFF")
        except Exception as exc:
            self.led_var.set(f"LEDエラー: {exc}")
            self._append_log(f"LEDエラー: {exc}")

    def turn_off_leds(self) -> None:
        self._turn_off_leds()
        for key in self.button_states:
            self.button_states[key] = False
        self._refresh_button_indicators()
        self._append_log("LED 全消灯")

    def _on_sleep_button_press_threadsafe(self) -> None:
        self.root.after(0, self._on_sleep_button_press)

    def _on_sleep_button_release_threadsafe(self) -> None:
        self.root.after(0, self._on_sleep_button_release)

    def _on_sleep_button_press(self) -> None:
        self.sleep_button_var.set("押下中")
        self.sleep_press_time = time.monotonic()
        self.sleep_long_press_triggered = False
        self._append_log("上部ボタン 押下")
        self.root.after(100, self._check_sleep_long_press)

    def _on_sleep_button_release(self) -> None:
        if not self.sleep_long_press_triggered:
            self.sleep_button_var.set("離上")
            self._append_log("上部ボタン 離上")

        self.sleep_press_time = None

    def _check_sleep_long_press(self) -> None:
        if self.sleep_press_time is None:
            return

        if self.sleep_long_press_triggered:
            return

        elapsed_ms = (time.monotonic() - self.sleep_press_time) * 1000
        if elapsed_ms >= self.sleep_long_press_ms:
            self.sleep_long_press_triggered = True
            self.sleep_button_var.set("長押し")
            self._append_log("上部ボタン 長押し検出")
            self._show_shutdown_dialog()
        else:
            self.root.after(100, self._check_sleep_long_press)

    def _show_shutdown_dialog(self) -> None:
        result = messagebox.askokcancel(
            "シャットダウン確認",
            "reTerminal をシャットダウンしますか？",
            parent=self.root,
        )

        if result:
            self._append_log("シャットダウン実行")
            self._shutdown_system()
        else:
            self._append_log("シャットダウン取消")
            self.sleep_button_var.set("取消")

    def _shutdown_system(self) -> None:
        try:
            subprocess.Popen(
                ["sudo", "-n", "systemctl", "poweroff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            self._append_log(f"シャットダウン失敗: {exc}")
            self.sleep_button_var.set("失敗")

    def _make_info_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=f"{label}:", style="Info.TLabel", width=7).grid(
            row=row, column=0, sticky="w", padx=(0, 6), pady=3
        )
        ttk.Label(parent, textvariable=variable, style="Value.TLabel").grid(
            row=row, column=1, sticky="w", pady=3
        )
        parent.columnconfigure(1, weight=1)

    def _append_log(self, message: str) -> None:
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def _submit_coro(self, coro) -> None:
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def _safe_ui(self, func) -> None:
        self.root.after(0, func)

    def scan_ble(self) -> None:
        async def _task() -> None:
            try:
                results = await self.ble.scan()
                lines = [f"{r.name or '(no name)'} / {r.address}" for r in results]
                if not lines:
                    self._safe_ui(lambda: self._append_log("BLE scan: デバイスなし"))
                    self._safe_ui(lambda: self.status_var.set("BLE scan: デバイスなし"))
                    return

                def _update() -> None:
                    self.status_var.set(f"BLE scan: {len(lines)}件")
                    self._append_log("BLE scan 結果:")
                    for line in lines:
                        self._append_log(f"  {line}")

                self._safe_ui(_update)
            except Exception as exc:
                self._safe_ui(lambda: self.status_var.set(f"BLE scan 失敗: {exc}"))
                self._safe_ui(lambda: self._append_log(f"BLE scan 失敗: {exc}"))

        self._submit_coro(_task())

    def connect_ble(self) -> None:
        async def _task() -> None:
            try:
                ok = await self.ble.connect()
                if not ok:
                    self._safe_ui(lambda: self.ble_var.set("BLE: 対象未検出"))
                    self._safe_ui(lambda: self.status_var.set("BLE接続失敗"))
                    self._safe_ui(lambda: self._append_log(f"{self.config.ble_device_name} が見つかりません"))
                    return

                await self.ble.start_notify(self._notify_handler)
                await self.ble.send_text("*IDN?")
                self._safe_ui(lambda: self.ble_var.set("BLE: 接続中"))
                self._safe_ui(lambda: self.status_var.set("BLE接続成功"))
                self._safe_ui(lambda: self._append_log("BLE接続成功"))
            except Exception as exc:
                self._safe_ui(lambda: self.ble_var.set("BLE: エラー"))
                self._safe_ui(lambda: self.status_var.set(f"BLE接続失敗: {exc}"))
                self._safe_ui(lambda: self._append_log(f"BLE接続失敗: {exc}"))

        self._submit_coro(_task())

    def disconnect_ble(self) -> None:
        async def _task() -> None:
            try:
                await self.ble.stop_notify()
                await self.ble.disconnect()
                self._safe_ui(lambda: self.ble_var.set("BLE: 未接続"))
                self._safe_ui(lambda: self.status_var.set("BLE切断"))
                self._safe_ui(lambda: self._append_log("BLE切断"))
            except Exception as exc:
                self._safe_ui(lambda: self.status_var.set(f"BLE切断失敗: {exc}"))
                self._safe_ui(lambda: self._append_log(f"BLE切断失敗: {exc}"))

        self._submit_coro(_task())

    def send_ping(self) -> None:
        async def _task() -> None:
            try:
                await self.ble.send_text("*IDN?")
                self._safe_ui(lambda: self.status_var.set("IDN送信"))
                self._safe_ui(lambda: self._append_log("送信: *IDN?"))
            except Exception as exc:
                self._safe_ui(lambda: self.status_var.set(f"送信失敗: {exc}"))
                self._safe_ui(lambda: self._append_log(f"送信失敗: {exc}"))

        self._submit_coro(_task())

    def _notify_handler(self, _sender: int, data: bytearray) -> None:
        text = data.decode("utf-8", errors="ignore")

        def _update() -> None:
            self.recv_var.set(text)
            self.status_var.set("BLE受信")
            self._append_log(f"受信: {text}")

            if text.startswith("WIO:BTN "):
                self.button_var.set(text)

        self._safe_ui(_update)

    def on_close(self) -> None:
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

        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()