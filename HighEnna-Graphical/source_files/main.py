from PyQt6.QtWidgets import QApplication
import sys
import os

from gui import *

if __name__ == "__main__":
    init_path = None
    if len(sys.argv) > 2:
        sys.exit()
    elif len(sys.argv) > 1:
        arg = sys.argv[1]
        if not os.path.exists(arg): sys.exit()
        if os.path.isfile(arg):
            init_path = os.path.abspath(os.path.dirname(arg))
        elif os.path.isdir(arg):
            # Check if directory contains a '.heproj' file
            contains_heproj = any(f.endswith('.heproj') for f in os.listdir(arg))
            if not contains_heproj:sys.exit()
            init_path = os.path.abspath(arg)
    app = QApplication(sys.argv)
    window = MainWindow(init_path)
    window.show()
    sys.exit(app.exec())