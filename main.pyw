"""
main.py
Поєднує CreditCalculatorApp → LoanController → UserInterface.
"""
import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_PATH = os.path.join(BASE_DIR, "app.log")

import sys
import logging
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from controller import LoanController
from view import UserInterface

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

APP_ID = "bankvault_calculator_instance"

socket = QLocalSocket()
socket.connectToServer(APP_ID)

# якщо вже запущено
if socket.waitForConnected(100):
    socket.write(b"activate")
    socket.flush()
    socket.waitForBytesWritten(100)
    sys.exit(0)

server = QLocalServer()
server.listen(APP_ID)

class CreditCalculatorApp:
    """
    Кореневий об’єкт застосунку.
    Містить QApplication, LoanController та UserInterface.
    """

    def __init__(self, argv: list[str]) -> None:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,   True)

        self._app = QApplication(argv)
        self._app.setStyle("Fusion")
        self._app.setPalette(self._dark_palette())

        self._controller = LoanController()
        self._window     = UserInterface(self._controller)

        server.newConnection.connect(self.activate_existing)

        logger.info("CreditCalculatorApp initialized")

    def run(self) -> int:
        self._window.show()
        logger.info("Window shown: entering event loop")
        return self._app.exec_()
    
    def activate_existing(self):
        self._window.setWindowState(
            self._window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
        )
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    @staticmethod
    def _dark_palette() -> QPalette:
        pal = QPalette()
        pal.setColor(QPalette.Window,          QColor("#080d24"))
        pal.setColor(QPalette.WindowText,      QColor("#e8f0ff"))
        pal.setColor(QPalette.Base,            QColor("#0a1233"))
        pal.setColor(QPalette.AlternateBase,   QColor("#0d1b4b"))
        pal.setColor(QPalette.Text,            QColor("#e8f0ff"))
        pal.setColor(QPalette.Button,          QColor("#1a2a5a"))
        pal.setColor(QPalette.ButtonText,      QColor("#e8f0ff"))
        pal.setColor(QPalette.Highlight,       QColor("#1e6fff"))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        pal.setColor(QPalette.ToolTipBase,     QColor("#0d1b4b"))
        pal.setColor(QPalette.ToolTipText,     QColor("#e8f0ff"))
        return pal


def main() -> None:
    app = CreditCalculatorApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
