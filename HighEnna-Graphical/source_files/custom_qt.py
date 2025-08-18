from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import re

class TabSearchDialog(QDialog):
    def __init__(self, parent: 'CustomTabWidget'):
        super().__init__(parent)
        self.setWindowTitle("Search Tabs")
        self.setMinimumSize(300, 400)
        self.tab_widget = parent

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter regex to search tabs...")
        self.search_bar.textChanged.connect(self.update_list)

        self.result_list = QListWidget(self)
        self.result_list.itemActivated.connect(self.select_tab)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.result_list)

        self.update_list()
        self.adjust_size()

    def update_list(self):
        pattern = self.search_bar.text()
        self.result_list.clear()

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return  # Ignore invalid regex

        for index, full_title in enumerate(self.tab_widget.full_titles):
            if regex.search(full_title):
                item = QListWidgetItem(full_title)
                item.setData(Qt.ItemDataRole.UserRole, index)
                self.result_list.addItem(item)

    def select_tab(self, item: QListWidgetItem):
        index = item.data(Qt.ItemDataRole.UserRole)
        self.tab_widget.setCurrentIndex(index)
        self.accept()

    def adjust_size(self):
        if self.isMaximized():
            return

        item_count = self.result_list.count()

        if item_count == 0:
            return

        # Measure the widest list item
        max_label_width = 0
        for i in range(item_count):
            item = self.result_list.item(i)
            max_label_width = max(max_label_width, self.result_list.fontMetrics().boundingRect(item.text()).width())

        # Add room for scrollbar and margins
        total_width = max_label_width + 60

        # Assume approx 30px per item, up to 10 items visible
        visible_items = min(item_count, 10)
        total_height = 50 + 30 * visible_items + self.search_bar.sizeHint().height()

        # Ensure not smaller than current size (avoid shrinking)
        total_width = max(total_width, self.width())
        total_height = max(total_height, self.height())

        # Constrain to screen
        current_screen = QApplication.screenAt(self.geometry().center())
        if current_screen:
            available_geometry = current_screen.availableGeometry()
        else:
            available_geometry = QApplication.primaryScreen().availableGeometry()

        total_width = min(total_width, available_geometry.width() - 75)
        total_height = min(total_height, available_geometry.height() - 100)

        self.resize(total_width, total_height)


class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.full_titles: list[str] = []

        self.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self.on_tabbar_context_menu)

    def addTab(self, widget: QWidget, full_title: str):
        tab_title = full_title[:20] + "..." if len(full_title) > 20 else full_title
        index = super().addTab(widget, tab_title)
        self.full_titles.insert(index, full_title)
        return index

    def insertTab(self, index: int, widget: QWidget, full_title: str):
        tab_title = full_title[:20] + "..." if len(full_title) > 20 else full_title
        index = super().insertTab(index, widget, tab_title)
        self.full_titles.insert(index, full_title)
        return index

    def removeTab(self, index: int):
        super().removeTab(index)
        del self.full_titles[index]

    def on_tabbar_context_menu(self, pos: QPoint):
        tabbar = self.tabBar()
        menu = QMenu(tabbar)

        # Add search action
        search_action = menu.addAction("🔍 Search Tabs...")
        search_action.triggered.connect(self.open_search_dialog)
        menu.addSeparator()

        # Add tab titles (full titles)
        for i, full_title in enumerate(self.full_titles):
            action = menu.addAction(full_title)
            action.triggered.connect(lambda checked=False, index=i: self.setCurrentIndex(index))

        global_pos = tabbar.mapToGlobal(pos)
        menu.exec(global_pos)

    def open_search_dialog(self):
        dialog = TabSearchDialog(self)
        dialog.exec()

class CustomModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = Table()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.table.data) if hasattr(self.table, 'data') else 0

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.table.column_names) if hasattr(self.table, 'column_names') else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        return self.table.get_cell(index.row(), index.column())

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self.table.set_cell([(index.row(), index.column(), value)])
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        if sourceRow == destinationChild or count != 1:
            return False

        self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, destinationChild)
        self.table.swap_rows([(sourceRow, destinationChild)])
        self.endMoveRows()
        return True


    # Forwarding methods
    def undo(self):
        self.table.undo()
        self.modelReset.emit()

    def redo(self):
        self.table.redo()
        self.modelReset.emit()

    def insert_column(self, items):
        self.table.insert_column(items)
        self.modelReset.emit()

    def remove_column(self, items):
        self.table.remove_column(items)
        self.modelReset.emit()

    def insert_row(self, items):
        self.table.insert_row(items)
        self.modelReset.emit()

    def duplicate_row(self, items):
        self.table.duplicate_row(items)
        self.modelReset.emit()

    def remove_row(self, items):
        self.table.remove_row(items)
        self.modelReset.emit()

    def set_cell(self, items):
        self.table.set_cell(items)
        self.modelReset.emit()

    def swap_columns(self, items):
        self.table.swap_columns(items)
        self.modelReset.emit()

    def swap_rows(self, items):
        self.table.swap_rows(items)
        self.modelReset.emit()

class ReorderableHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsMovable(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        old = self.logicalIndex(self.draggedSection())
        new = self.logicalIndexAt(event.position().toPoint())

        if old != new and old != -1 and new != -1:
            self.parent().swap_columns((old, new))
            event.accept()

class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_ = CustomModel(self)
        self.setModel(self.model_)

        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)

        self.setHorizontalHeader(ReorderableHeaderView(Qt.Orientation.Horizontal, self))


    # Forwarding to the model
    def undo(self):
        self.model_.undo()

    def redo(self):
        self.model_.redo()

    def insert_column(self, items):
        self.model_.insert_column(items)

    def remove_column(self, items):
        self.model_.remove_column(items)

    def insert_row(self, items):
        self.model_.insert_row(items)

    def duplicate_row(self, items):
        self.model_.duplicate_row(items)

    def remove_row(self, items):
        self.model_.remove_row(items)

    def set_cell(self, items):
        self.model_.set_cell(items)

    def swap_columns(self, items):
        self.model_.swap_columns(items)

    def swap_rows(self, items):
        self.model_.swap_rows(items)