from __future__ import annotations

from collections.abc import Callable

try:
    from gpiozero import Button
except Exception:  # pragma: no cover
    Button = None  # type: ignore


ButtonCallback = Callable[[int], None]


class FrontButtons:
    """
    reTerminal 前面ボタンの入力管理。
    GPIO が使えない場合は mock モードで起動できる。
    """

    def __init__(self, pins: list[int], on_press: ButtonCallback, allow_mock: bool = True) -> None:
        self._pins = pins
        self._on_press = on_press
        self._allow_mock = allow_mock
        self._buttons: list[Button] = []
        self._mock_mode = False
        self._init_error = ""

        self._initialize()

    def _initialize(self) -> None:
        if Button is None:
            self._init_error = "gpiozero が利用できません"
            if self._allow_mock:
                self._mock_mode = True
                return
            raise RuntimeError(self._init_error)

        try:
            for index, pin in enumerate(self._pins, start=1):
                btn = Button(pin, pull_up=True, bounce_time=0.05)
                btn.when_pressed = lambda idx=index: self._on_press(idx)
                self._buttons.append(btn)
        except Exception as exc:
            self._init_error = f"GPIO 初期化失敗: {exc}"
            self.close()
            if self._allow_mock:
                self._mock_mode = True
            else:
                raise

    @property
    def mock_mode(self) -> bool:
        return self._mock_mode

    @property
    def init_error(self) -> str:
        return self._init_error

    def simulate_press(self, index: int) -> None:
        self._on_press(index)

    def close(self) -> None:
        for btn in self._buttons:
            try:
                btn.close()
            except Exception:
                pass
        self._buttons.clear()