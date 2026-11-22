import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from .main_window import MainWindow
from .styles import GLOBAL_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    apply_stylesheet(app, theme="light_blue.xml")
    window = MainWindow(app)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
