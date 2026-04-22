from __future__ import annotations

from app.config import AppConfig
from app.controller import AppController
from app.gui import MainWindow


def main() -> None:
    config = AppConfig()
    gui = MainWindow(config)
    controller = AppController(config, gui)
    gui.set_controller(controller)
    controller.start()
    gui.run()


if __name__ == "__main__":
    main()