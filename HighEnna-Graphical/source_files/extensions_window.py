from PyQt6.QtWidgets import (
    QTableWidgetItem, QMessageBox, QWidget, QSizePolicy, QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget
)
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QSize
import re


class ExtensionsWindow(QDialog):
    configAccepted = pyqtSignal(dict)

    def __init__(self, parent, config=None):

        super().__init__(parent)
        self.setWindowTitle("Extensions Manager")

        main_layout = QHBoxLayout(self)
        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Scenario", "Script"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        # Buttons
        btn_layout = QVBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_remove = QPushButton("Remove")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addStretch(1)
        self.btn_apply = QPushButton("Apply")
        btn_layout.addWidget(self.btn_apply)
        main_layout.addLayout(btn_layout)

        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Connections
        self.btn_add.clicked.connect(self.add_entry)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_apply.clicked.connect(self.apply_config)

        # Populate if provided
        if config:
            for scenario, script in config.items():
                self.add_entry(scenario, script)

        self.adjust_size()

    def add_entry(self, scenario="", script=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(scenario))
        self.table.setItem(row, 1, QTableWidgetItem(script))

    def remove_selected(self):
        selected = sorted(set(i.row() for i in self.table.selectedIndexes()), reverse=True)
        for row in selected:
            self.table.removeRow(row)

    def apply_config(self):
        config = {}
        invalid_entries = []

        for row in range(self.table.rowCount()):
            scenario_item = self.table.item(row, 0)
            script_item = self.table.item(row, 1)
            scenario = scenario_item.text().strip() if scenario_item else ""
            script = script_item.text().strip() if script_item else ""

            # Validate: both must match r'^\.\w+$'
            if not re.fullmatch(r'\.\w+', scenario) or not re.fullmatch(r'\.\w+', script):
                invalid_entries.append((row + 1, scenario, script))
            else:
                config[scenario] = script

        if invalid_entries:
            msg = "Invalid entries:\n\n" + "\n".join(
                f"Row {r}: Scenario='{s}' Script='{sc}'" for r, s, sc in invalid_entries
            )
            QMessageBox.warning(self, "Invalid Entries", msg)
            return

        self.configAccepted.emit(config)
        self.accept()

    def adjust_size(self):
        numer1, denom1 = 5, 7
        numer2, denom2 = 7, 8

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()

        available_geometry = screen.availableGeometry()
        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        max_width = screen_width * numer1 // denom1
        max_height = screen_height * numer2 // denom2

        # if self.table:
        #     self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # Compute table's size like in CTableWidget.sizeHint()
        total_width = self.table.verticalHeader().width()
        for col in range(self.table.columnCount()):
            total_width += self.table.columnWidth(col)

        total_height = self.table.horizontalHeader().height()
        for row in range(self.table.rowCount()):
            total_height += self.table.rowHeight(row)

        total_width += 2 * self.table.frameWidth() + 35
        total_height += 2 * self.table.frameWidth() + 10

        # Add button column width and layout padding
        btn_col_width = max(
            self.btn_add.sizeHint().width(),
            self.btn_remove.sizeHint().width(),
            self.btn_apply.sizeHint().width(),
        )
        total_width += btn_col_width + 40  # spacing + margins

        # Add vertical button stack height (but don’t exceed table height too much)
        btns_height = (
            self.btn_add.sizeHint().height()
            + self.btn_remove.sizeHint().height()
            + self.btn_apply.sizeHint().height()
            + 60  # spacing/margins between buttons
        )
        total_height = max(total_height, btns_height)

        new_width = min(total_width + 15, max_width)
        new_height = min(total_height + 15, max_height)

        new_x = available_geometry.x() + (screen_width - new_width) // 2
        new_y = available_geometry.y() + (screen_height - new_height) // 2

        self.setGeometry(new_x, new_y, new_width, new_height)


