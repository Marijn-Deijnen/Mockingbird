import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.app import MainWindow
from src.paths import assets_dir

ICON_PATH = assets_dir() / "icon.png"
STYLE_PATH = assets_dir() / "style.qss"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mockingbird")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    if STYLE_PATH.exists():
        app.setStyleSheet(STYLE_PATH.read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
