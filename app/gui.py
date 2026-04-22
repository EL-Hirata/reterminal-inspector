from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from app.config import AppConfig


class MainWindow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.controller = None

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
        self.keymap_var = tk.StringVar(value="F1→A / F2→B / F3→C / ○短押し=BLE接続 / ○長押し3秒=Shutdown")
        self.led_var = tk.StringVar(value="LED: 初期化前")

        self.button_widgets: dict[str, dict[str, tk.Widget]] = {}

        self._build_ui()
        self._bind_keys()

    def set_controller(self, controller) -> None:
        self.controller = controller

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text=self.config.window_title, style="Title.TLabel")
        title.pack(anchor="w", pady=(0, 4))

        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 6))

        top.columnconfigure(0, weight=3)
        top.columnconfigure(1, weight=4)

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

        log_frame = ttk.LabelFrame(right_top, text="ログ", padding=8, style="Section.TLabelframe")
        log_frame.pack(fill="both", expand=True)

        self.log_text = ScrolledText(log_frame, height=12, font=("", 12))
        self.log_text.pack(fill="both", expand=True)

        action_frame = ttk.LabelFrame(main, text="操作", padding=10, style="Section.TLabelframe")
        action_frame.pack(fill="x", pady=(0, 8))

        ttk.Button(
            action_frame, text="BLEスキャン", command=lambda: self.controller.scan_ble(), style="Big.TButton"
        ).grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        ttk.Button(
            action_frame, text="BLE接続", command=lambda: self.controller.connect_ble(), style="Big.TButton"
        ).grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ttk.Button(
            action_frame, text="IDN送信", command=lambda: self.controller.send_idn(), style="Big.TButton"
        ).grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        ttk.Button(
            action_frame, text="BLE切断", command=lambda: self.controller.disconnect_ble(), style="Big.TButton"
        ).grid(row=0, column=3, padx=8, pady=8, sticky="ew")
        ttk.Button(
            action_frame, text="LED全消灯", command=lambda: self.controller.turn_off_leds(), style="Big.TButton"
        ).grid(row=0, column=4, padx=8, pady=8, sticky="ew")
        ttk.Button(
            action_frame, text="終了", command=self.on_close, style="Big.TButton"
        ).grid(row=0, column=5, padx=8, pady=8, sticky="ew")

        for col in range(6):
            action_frame.columnconfigure(col, weight=1)

        button_frame = ttk.LabelFrame(main, text="物理ボタン状態", padding=8, style="Section.TLabelframe")
        button_frame.pack(fill="x")

        ttk.Label(
            button_frame,
            text="F1→Wio A / F2→Wio B / F3→Wio C / ○短押し=BLE接続 / ○長押し3秒=Shutdown",
            font=("", 11, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        indicator_frame = ttk.Frame(button_frame)
        indicator_frame.pack(fill="x")

        self._create_indicator(indicator_frame, 0, "F1", "a")
        self._create_indicator(indicator_frame, 1, "F2", "s")
        self._create_indicator(indicator_frame, 2, "F3", "d")
        self._create_indicator(indicator_frame, 3, "○", "f")

    def _bind_keys(self) -> None:
        self.root.bind("<Button-1>", lambda _e: self.root.focus_force())
        self.root.after(300, self.root.focus_force)

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

    def set_indicator(self, button_name: str, is_on: bool) -> None:
        widgets = self.button_widgets[button_name]
        key_name = {
            "F1": "a",
            "F2": "s",
            "F3": "d",
            "○": "f",
        }[button_name]

        outer = widgets["outer"]
        title = widgets["title"]
        inner = widgets["inner"]

        if is_on:
            outer.config(bg="#00a844")
            title.config(bg="#00a844", fg="white")
            inner.config(bg="#00c853", fg="white", text=f"{key_name}\nON")
        else:
            outer.config(bg="#505050")
            title.config(bg="#505050", fg="white")
            inner.config(bg="#808080", fg="white", text=f"{key_name}\nOFF")

        self.root.update_idletasks()

    def ask_shutdown_dialog(self) -> bool:
        result = {"ok": False}

        dialog = tk.Toplevel(self.root)
        dialog.title("シャットダウン確認")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#202020")
        dialog.geometry("700x320")
        dialog.resizable(False, False)

        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        dlg_w = 700
        dlg_h = 320
        pos_x = parent_x + max((parent_w - dlg_w) // 2, 0)
        pos_y = parent_y + max((parent_h - dlg_h) // 2, 0)
        dialog.geometry(f"{dlg_w}x{dlg_h}+{pos_x}+{pos_y}")

        frame = tk.Frame(dialog, bg="#202020", padx=24, pady=24)
        frame.pack(fill="both", expand=True)

        title_label = tk.Label(
            frame,
            text="シャットダウン確認",
            font=("", 22, "bold"),
            bg="#202020",
            fg="white",
        )
        title_label.pack(pady=(0, 20))

        msg_label = tk.Label(
            frame,
            text="reTerminal をシャットダウンしますか？",
            font=("", 18, "bold"),
            bg="#202020",
            fg="white",
        )
        msg_label.pack(pady=(0, 28))

        btn_frame = tk.Frame(frame, bg="#202020")
        btn_frame.pack(fill="x", pady=(10, 0))

        def on_ok() -> None:
            result["ok"] = True
            dialog.destroy()

        def on_cancel() -> None:
            result["ok"] = False
            dialog.destroy()

        ok_button = tk.Button(
            btn_frame,
            text="OK",
            font=("", 18, "bold"),
            width=10,
            height=2,
            bg="#00c853",
            fg="white",
            activebackground="#00a844",
            activeforeground="white",
            relief="raised",
            bd=3,
            command=on_ok,
        )
        ok_button.pack(side="left", expand=True, padx=20)

        cancel_button = tk.Button(
            btn_frame,
            text="キャンセル",
            font=("", 18, "bold"),
            width=10,
            height=2,
            bg="#666666",
            fg="white",
            activebackground="#555555",
            activeforeground="white",
            relief="raised",
            bd=3,
            command=on_cancel,
        )
        cancel_button.pack(side="right", expand=True, padx=20)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.bind("<Escape>", lambda _e: on_cancel())
        ok_button.focus_set()

        self.root.wait_window(dialog)
        return result["ok"]

    def _make_info_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=f"{label}:", style="Info.TLabel", width=7).grid(
            row=row, column=0, sticky="w", padx=(0, 6), pady=3
        )
        ttk.Label(parent, textvariable=variable, style="Value.TLabel").grid(
            row=row, column=1, sticky="w", pady=3
        )
        parent.columnconfigure(1, weight=1)

    def append_log(self, message: str) -> None:
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def set_ble_text(self, text: str) -> None:
        self.ble_var.set(text)

    def set_recv_text(self, text: str) -> None:
        self.recv_var.set(text)

    def set_button_text(self, text: str) -> None:
        self.button_var.set(text)

    def set_led_text(self, text: str) -> None:
        self.led_var.set(text)

    def on_close(self) -> None:
        if self.controller is not None:
            self.controller.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()