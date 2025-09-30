from PyQt6.QtWidgets import QApplication
import sys

from gui import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())