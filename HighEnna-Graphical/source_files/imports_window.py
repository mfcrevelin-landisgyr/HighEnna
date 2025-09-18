from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *

class ImportsWindow(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, parent, receivers, assignees, relations=None):
        super().__init__(parent)
        self.setWindowTitle("Imports Assignment Editor")

        self.receivers = receivers
        self.assignees = assignees

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.table = CTableWidget(receivers, assignees, relations)
        layout.addWidget(self.table)

        hbox = QHBoxLayout()
        hbox.addStretch()
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(120)
        apply_btn.clicked.connect(self.on_apply)
        hbox.addWidget(apply_btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

        self.adjust_size()

    def on_apply(self):
        relations = {}
        for row, receiver in enumerate(self.receivers):
            assigned = set()
            for col, assignee in enumerate(self.assignees):
                checkbox_widget = self.table.cellWidget(row, col)
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if checkbox.isChecked():
                    assigned.add(assignee)
            relations[receiver] = assigned
        self.applied.emit(relations)
        self.close()

    def adjust_size(self):
        numer, denom = 5, 7

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()

        available_geometry = screen.availableGeometry()

        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        max_width = screen_width * numer // denom
        max_height = screen_height * numer // denom

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        content_size = self.sizeHint()

        new_width = min(content_size.width(), max_width)
        new_height = min(content_size.height(), max_height)

        new_x = available_geometry.x() + (screen_width - new_width) // 2
        new_y = available_geometry.y() + (screen_height - new_height) // 2

        self.setGeometry(new_x, new_y, new_width, new_height)

