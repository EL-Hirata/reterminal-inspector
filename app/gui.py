from __future__ import annotations

import tkinter as tk


class MainWindow:
    def __init__(self, config) -> None:
        self.config = config
        self.controller = None

        self.root = tk.Tk()
        self.root.title(self.config.window_title)
        self.root.geometry(self.config.window_size)
        self.root.configure(bg="#111111")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.update_idletasks()
        self.root.attributes("-fullscreen", True)

        self.status_var = tk.StringVar(value="待機中")
        self.ble_var = tk.StringVar(value="BLE: 未接続")
        self.recv_var = tk.StringVar(value="-")
        self.led_var = tk.StringVar(value="LED: 初期化前")

        self.log_lines: list[str] = []

        self.canvas = tk.Canvas(
            self.root,
            bg="#111111",
            highlightthickness=0,
            width=1280,
            height=720,
        )
        self.canvas.pack(fill="both", expand=True)

        self.toolbar = tk.Frame(self.root, bg="#222222")
        self.toolbar.place(x=16, y=635)

        self.scan_button = tk.Button(
            self.toolbar,
            text="BLEスキャン",
            font=("", 14, "bold"),
            width=13,
            height=3,
            command=lambda: self.controller.scan_ble() if self.controller else None,
        )
        self.scan_button.grid(row=0, column=0, padx=6, pady=6)

        self.connect_button = tk.Button(
            self.toolbar,
            text="BLE接続",
            font=("", 14, "bold"),
            width=13,
            height=3,
            command=lambda: self.controller.connect_ble() if self.controller else None,
        )
        self.connect_button.grid(row=0, column=1, padx=6, pady=6)

        self.idn_button = tk.Button(
            self.toolbar,
            text="IDN送信",
            font=("", 14, "bold"),
            width=13,
            height=3,
            command=lambda: self.controller.send_idn() if self.controller else None,
        )
        self.idn_button.grid(row=0, column=2, padx=6, pady=6)

        self.disconnect_button = tk.Button(
            self.toolbar,
            text="BLE切断",
            font=("", 14, "bold"),
            width=13,
            height=3,
            command=lambda: self.controller.disconnect_ble() if self.controller else None,
        )
        self.disconnect_button.grid(row=0, column=3, padx=6, pady=6)

        self.exit_button = tk.Button(
            self.toolbar,
            text="終了",
            font=("", 14, "bold"),
            width=11,
            height=3,
            bg="#aa3333",
            fg="white",
            activebackground="#882222",
            activeforeground="white",
            command=self.on_close,
        )
        self.exit_button.grid(row=0, column=4, padx=6, pady=6)

        self._bind_keys()

    def set_controller(self, controller) -> None:
        self.controller = controller

    def _bind_keys(self) -> None:
        self.root.bind("<Button-1>", lambda _e: self.root.focus_force())
        self.root.after(300, self.root.focus_force)

    def on_close(self) -> None:
        if self.controller is not None:
            self.controller.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    def append_log(self, message: str) -> None:
        self.log_lines.append(message)
        self.log_lines = self.log_lines[-10:]

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def set_ble_text(self, text: str) -> None:
        self.ble_var.set(text)

    def set_recv_text(self, text: str) -> None:
        self.recv_var.set(text)

    def set_led_text(self, text: str) -> None:
        self.led_var.set(text)

    def ask_shutdown_dialog(self) -> bool:
        result = {"ok": False}

        dialog = tk.Toplevel(self.root)
        dialog.title("シャットダウン確認")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#202020")
        dialog.geometry("760x340")
        dialog.resizable(False, False)

        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        dlg_w = 760
        dlg_h = 340
        pos_x = parent_x + max((parent_w - dlg_w) // 2, 0)
        pos_y = parent_y + max((parent_h - dlg_h) // 2, 0)
        dialog.geometry(f"{dlg_w}x{dlg_h}+{pos_x}+{pos_y}")

        frame = tk.Frame(dialog, bg="#202020", padx=24, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="シャットダウン確認",
            font=("", 24, "bold"),
            bg="#202020",
            fg="white",
        ).pack(pady=(0, 20))

        tk.Label(
            frame,
            text="reTerminal をシャットダウンしますか？",
            font=("", 20, "bold"),
            bg="#202020",
            fg="white",
        ).pack(pady=(0, 30))

        btn_frame = tk.Frame(frame, bg="#202020")
        btn_frame.pack(fill="x")

        def on_ok() -> None:
            result["ok"] = True
            dialog.destroy()

        def on_cancel() -> None:
            result["ok"] = False
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="OK",
            font=("", 18, "bold"),
            width=12,
            height=2,
            bg="#00c853",
            fg="white",
            activebackground="#00a844",
            activeforeground="white",
            bd=3,
            command=on_ok,
        ).pack(side="left", expand=True, padx=20)

        tk.Button(
            btn_frame,
            text="キャンセル",
            font=("", 18, "bold"),
            width=12,
            height=2,
            bg="#666666",
            fg="white",
            activebackground="#555555",
            activeforeground="white",
            bd=3,
            command=on_cancel,
        ).pack(side="right", expand=True, padx=20)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.bind("<Escape>", lambda _e: on_cancel())

        self.root.wait_window(dialog)
        return result["ok"]

    def render(self, state) -> None:
        c = self.canvas
        c.delete("all")

        w = max(self.root.winfo_width(), 1280)
        h = max(self.root.winfo_height(), 720)

        c.create_rectangle(0, 0, w, h, fill="#111111", outline="")

        self._draw_panel(20, 20, 380, 165, "SYSTEM")
        self._draw_panel(420, 20, 380, 165, "SENSOR")
        self._draw_panel(820, 20, 430, 290, "WIO BUTTONS")
        self._draw_panel(20, 200, 780, 130, "reTerminal BUTTONS")
        self._draw_panel(20, 345, 1230, 275, "COMM / LOG")

        self._draw_system_panel(state)
        self._draw_sensor_panel(state)
        self._draw_wio_buttons_panel(state)
        self._draw_rt_buttons_panel(state)
        self._draw_comm_panel(state)

    def _draw_panel(self, x: int, y: int, w: int, h: int, title: str) -> None:
        self.canvas.create_rectangle(x, y, x + w, y + h, outline="#666666", width=2, fill="#1b1b1b")
        self.canvas.create_rectangle(x, y, x + w, y + 30, outline="", fill="#333333")
        self.canvas.create_text(
            x + 10, y + 15,
            anchor="w",
            text=title,
            fill="white",
            font=("", 14, "bold"),
        )

    def _draw_label_value(self, x: int, y: int, label: str, value: str, color: str = "white") -> None:
        self.canvas.create_text(x, y, anchor="nw", text=label, fill="#bbbbbb", font=("", 12, "bold"))
        self.canvas.create_text(x + 110, y, anchor="nw", text=value, fill=color, font=("", 12, "bold"))

    def _draw_button_box(self, x: int, y: int, w: int, h: int, label: str, is_on: bool) -> None:
        fill = "#00c853" if is_on else "#2e2e2e"
        outline = "#00c853" if is_on else "#777777"
        text_color = "black" if is_on else "white"
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline, width=2)
        self.canvas.create_text(x + w / 2, y + h / 2, text=label, fill=text_color, font=("", 14, "bold"))

    def _draw_system_panel(self, state) -> None:
        self._draw_label_value(40, 65, "STATUS", state.device_status, "#00c853" if state.ble_connected else "#ff5252")
        self._draw_label_value(40, 93, "BLE", self.ble_var.get())
        self._draw_label_value(40, 121, "LED", "ON" if state.wio_led_on else "OFF", "#00c853" if state.wio_led_on else "#bbbbbb")
        self._draw_label_value(40, 149, "IDN", state.idn)

    def _draw_sensor_panel(self, state) -> None:
        self._draw_label_value(440, 65, "LIGHT", str(state.light), "#ffd54f")
        self._draw_label_value(440, 93, "AX", f"{state.ax:.2f}")
        self._draw_label_value(440, 121, "AY", f"{state.ay:.2f}")
        self._draw_label_value(440, 149, "AZ", f"{state.az:.2f}")

    def _draw_wio_buttons_panel(self, state) -> None:
        base_x = 860
        base_y = 65
        bw = 80
        bh = 40

        self._draw_button_box(base_x + 95, base_y, bw, bh, "UP", state.buttons["UP"])
        self._draw_button_box(base_x, base_y + 52, bw, bh, "LEFT", state.buttons["LEFT"])
        self._draw_button_box(base_x + 95, base_y + 52, bw, bh, "PRESS", state.buttons["PRESS"])
        self._draw_button_box(base_x + 190, base_y + 52, bw, bh, "RIGHT", state.buttons["RIGHT"])
        self._draw_button_box(base_x + 95, base_y + 104, bw, bh, "DOWN", state.buttons["DOWN"])

        self._draw_button_box(base_x + 10,  base_y + 190, bw, bh, "C", state.buttons["C"])
        self._draw_button_box(base_x + 102, base_y + 190, bw, bh, "B", state.buttons["B"])
        self._draw_button_box(base_x + 194, base_y + 190, bw, bh, "A", state.buttons["A"])

    def _draw_rt_buttons_panel(self, state) -> None:
        self.canvas.create_text(
            40, 240,
            anchor="nw",
            text="F1=SENS / F2=LED / F3=IDN / ○=BLE / 長押し=OFF",
            fill="#cccccc",
            font=("", 12, "bold"),
        )

        self._draw_button_box(90, 268, 92, 42, "F1", state.rt_buttons["F1"])
        self._draw_button_box(225, 268, 92, 42, "F2", state.rt_buttons["F2"])
        self._draw_button_box(360, 268, 92, 42, "F3", state.rt_buttons["F3"])
        self._draw_button_box(495, 268, 92, 42, "○", state.rt_buttons["○"])

    def _draw_comm_panel(self, state) -> None:
        self._draw_label_value(40, 385, "APP STATUS", self.status_var.get())
        self._draw_label_value(40, 413, "LAST RX", state.last_rx[:90])
        self._draw_label_value(40, 441, "LAST TX", state.last_tx[:90])
        self._draw_label_value(40, 469, "LED STATUS", self.led_var.get())

        log_x = 640
        log_y = 385
        self.canvas.create_text(
            log_x, log_y,
            anchor="nw",
            text="LOG",
            fill="#bbbbbb",
            font=("", 12, "bold"),
        )

        for i, line in enumerate(self.log_lines[-10:]):
            self.canvas.create_text(
                log_x, log_y + 24 + i * 17,
                anchor="nw",
                text=line[:70],
                fill="#dddddd",
                font=("", 11),
            )
