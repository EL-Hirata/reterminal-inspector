from __future__ import annotations

from app.config import AppConfig
from app.gui import MainWindow


def main() -> None:
    config = AppConfig()
    window = MainWindow(config)
    window.run()


if __name__ == "__main__":
    main()