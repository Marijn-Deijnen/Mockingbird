import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.app import MainWindow

ICON_PATH = Path(__file__).parent / "src" / "assets" / "icon.png"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mockingbird")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
