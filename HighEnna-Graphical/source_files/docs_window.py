from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QApplication
from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView

import sys
import os
#https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    try:
        # base_path = sys._MEIPASS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

APPLICATION_NAME = "High Enna"


class DocsWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("High Enna - Documentation")

        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Navigation buttons
        nav_layout = QHBoxLayout()

        # Add a spacer to push buttons to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Buttons with UTF-8 symbols
        back_btn = QPushButton("\u25C0")    # ◀
        forward_btn = QPushButton("\u25B6") # ▶
        reload_btn = QPushButton("\u27F3")  # ⟳
        home_btn = QPushButton("\u2302")    # ⌂ (home symbol)

        for btn in (home_btn, back_btn, forward_btn, reload_btn):
            font = btn.font()
            font.setPointSizeF(font.pointSizeF() * 1.5)  # scale by 1.5
            btn.setFont(font)
            nav_layout.addWidget(btn)

        nav_layout.addItem(spacer)

        main_layout.addLayout(nav_layout)

        # Web view
        webview = QWebEngineView()
        index_file = os.path.abspath(resource_path("assets\\html\\index.html"))
        webview.setUrl(QUrl.fromLocalFile(index_file))
        main_layout.addWidget(webview)

        # Connect buttons
        back_btn.clicked.connect(lambda: webview.back() if webview.history().canGoBack() else None)
        forward_btn.clicked.connect(lambda: webview.forward() if webview.history().canGoForward() else None)
        reload_btn.clicked.connect(webview.reload)
        home_btn.clicked.connect(lambda: webview.setUrl(QUrl.fromLocalFile(index_file)))

        self.adjust_size()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    def adjust_size(self):
        numer, denom = 6, 7

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()
        
        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        width = screen_width * numer // denom
        height = screen_height * numer // denom

        new_x = available_geometry.x() + (screen_width - width) // 2
        new_y = available_geometry.y() + (screen_height - height) // 2

        self.setGeometry(new_x, new_y, width, height)
