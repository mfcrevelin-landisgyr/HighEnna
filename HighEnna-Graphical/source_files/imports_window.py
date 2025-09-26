from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *


class ImportsWindow(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Imports Assignment Editor")

        self.receivers = []
        self.assignees = []
        self.relations = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.table = None
        self.table_container = QVBoxLayout()
        layout.addLayout(self.table_container)

        self.table = CTableWidget(self)
        self.table_container.addWidget(self.table)

        hbox = QHBoxLayout()
        hbox.addStretch()
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(120)
        apply_btn.clicked.connect(self.on_apply)
        hbox.addWidget(apply_btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

        self.update(True)
        self.adjust_size()

    def update(self,is_start=False):
        project = self.parent().project

        receivers = sorted(project.tpy_files.keys())
        if not receivers:
            CFooter.broadcast("Project has no template files.", 1500)
            self.close()

        assignees = project.project_cache["modules"]['modules_set']
        if not assignees:
            CFooter.broadcast("Project has no module files.", 1500)
            self.close()

        parent_relations = self.parent().project.project_cache["modules"]['module_assignments']

        if is_start:
            self.relations = parent_relations.copy()

        else:
            new_assignees = set(assignees) - set(self.assignees)
            self.relations = {
                    k: (self.relations.get(k, parent_relations.get(k, set()).copy()) | new_assignees)
                    for k in receivers
                }

        self.receivers = receivers.copy()
        self.assignees = assignees.copy()

        self.table.update_table()
        self.recursive_install_event_filter()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.table:
                self.table.clearSelection()
        return super().eventFilter(obj, event)

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
        self.applied.emit(self.relations)
        self.close()

    def recursive_install_event_filter(self):
        def _recursive_install_event_filter(widget):
            widget.installEventFilter(self)
            for child in widget.children():
                if isinstance(child, QWidget):
                    _recursive_install_event_filter(child)
        _recursive_install_event_filter(self)

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

        if self.table:
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
        content_size = self.sizeHint()

        new_width = min(content_size.width(), max_width)
        new_height = min(content_size.height(), max_height)

        new_x = available_geometry.x() + (screen_width - new_width) // 2
        new_y = available_geometry.y() + (screen_height - new_height) // 2

        self.setGeometry(new_x, new_y, new_width, new_height)
