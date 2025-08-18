from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from collections import deque
import json
import os
import re

APPLICATION_NAME = "High Enna"

# ====== Qt Classes ======

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
    def __init__(self, view, table_mode):
        super().__init__(view)

        self.main_window = view.main_window
        self.project = view.project
        self.tpy_file = view.tpy_file
        self.tab = view.tab
        self.view = view

        self.table_mode = table_mode

        self.table = Table()

    def rowCount(self, parent=QModelIndex()):
        return len(self.table.data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.table.column_names)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            row = index.row()
            col = index.column()
            return self.table.get_cell(row, col)
        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row = index.row()
        col = index.column()
        self.table.set_cell([(row, col, str(value))])
        self.dataChanged.emit(index, index, [role])
        self.table.print()
        return True

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsEditable |
            Qt.ItemFlag.ItemIsDragEnabled |
            Qt.ItemFlag.ItemIsDropEnabled
        )

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation != Qt.Orientation.Horizontal:
            if self.table_mode == 'vals':
                return ''
            return str(section)
        if 0 <= section < len(self.table.column_names):
            return self.table.column_names[section]
        return QVariant()

    def supportedDragActions(self):
        return Qt.DropAction.MoveAction

    def handle_column_move(self, from_index, to_index):
        if from_index == to_index:
            return
        self.beginResetModel()
        self.table.move_column([(from_index, to_index)])
        self.endResetModel()

    def handle_row_move(self, from_index, to_index):
        if from_index == to_index:
            return
        self.beginResetModel()
        self.table.move_row([(from_index, to_index)])
        self.endResetModel()

class CustomTableView(QTableView):
    def __init__(self, tab, table_mode):
        super().__init__(tab.main_widget)

        self.main_window = tab.main_window
        self.project = tab.project
        self.tpy_file = tab.tpy_file
        self.tab = tab

        self.table_mode = table_mode
        
        self.setMouseTracking(True)
        
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionsMovable(True)

        self.model_ = CustomModel(self, table_mode)
        self.setModel(self.model_)

        self.horizontalHeader().sectionMoved.connect(self._on_column_moved)
        self.verticalHeader().sectionMoved.connect(self._on_row_moved)

    def wheelEvent(self, event: QWheelEvent):
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                delta = event.angleDelta().y()
                scrollbar = self.horizontalScrollBar()
            else:
                delta = event.angleDelta().y()
                scrollbar = self.verticalScrollBar()

            steps = delta // 120
            scrollbar.setValue(scrollbar.value() - steps * scrollbar.singleStep())

            event.accept()

    def _on_column_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        if self.model():
            self.model().handle_column_move(oldVisualIndex, newVisualIndex)

            header = self.horizontalHeader()
            header.blockSignals(True)
            for logical_index in range(header.count()):
                visual_index = header.visualIndex(logical_index)
                if visual_index != logical_index:
                    header.moveSection(visual_index, logical_index)
            header.blockSignals(False)

            self.model_.table.print()

    def _on_row_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        if self.model():
            self.model().handle_row_move(oldVisualIndex, newVisualIndex)

            header = self.verticalHeader()
            header.blockSignals(True)
            for logical_index in range(header.count()):
                visual_index = header.visualIndex(logical_index)
                if visual_index != logical_index:
                    header.moveSection(visual_index, logical_index)
            header.blockSignals(False)

            self.model_.table.print()

# ====== Other Classes ======

class Table:
    def __init__(self):
        self.column_names = []
        self.data = []

        self.undo_stack = deque()
        self.redo_stack = deque()

        # For undo/redo internal use
        self._last_op_data = {}

    def _record_undo(self, action, data):
        self.undo_stack.append((action, data))
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        action, data = self.undo_stack.pop()
        self.redo_stack.append((action, data))
        self._perform_undo(action, data)

    def redo(self):
        if not self.redo_stack:
            return
        action, data = self.redo_stack.pop()
        self.undo_stack.append((action, data))
        self._perform(action, data, record_undo=False)

    def _perform(self, action, data, record_undo=True):
        getattr(self, f"_{action}")(data, record_undo)

    def _perform_undo(self, action, data):
        getattr(self, f"_undo_{action}")(data)

    # --- Column Methods ---

    def insert_column(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._insert_column(items)

    def _insert_column(self, items, record_undo=True):
        undo_data = []

        for index, name in items:
            index = index if index <= len(self.data) else len(self.data)
            self.column_names.insert(index, name)
            for row in self.data:
                row.insert(index, "")
            undo_data.append((index, name))

        if record_undo:
            self._record_undo("insert_column", undo_data)

    def _undo_insert_column(self, items):
        for index, _ in reversed(items):
            self.column_names.pop(index)
            for row in self.data:
                row.pop(index)

    def remove_column(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._remove_column(items)

    def _remove_column(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            index = index if index < len(self.data) else len(self.data)-1
            name = self.column_names.pop(index)
            removed_cells = [row.pop(index) for row in self.data]
            undo_data.append((index, name, removed_cells))

        if record_undo:
            self._record_undo("remove_column", undo_data)

    def _undo_remove_column(self, items):
        for index, name, cells in reversed(items):
            self.column_names.insert(index, name)
            for i, row in enumerate(self.data):
                row.insert(index, cells[i])

    # --- Row Methods ---

    def insert_row(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._insert_row(items)

    def _insert_row(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            index = index if index <= len(self.data) else len(self.data)
            self.data.insert(index,['']*len(self.column_names))
            undo_data.append((index,))

        if record_undo:
            self._record_undo("insert_row", undo_data)

    def _undo_insert_row(self, items):
        for index, in reversed(items):
            self.data.pop(index)

    def remove_row(self, items):
        items = sorted(items, key=lambda x: x[0], reverse=True)
        self._remove_row(items)

    def _remove_row(self, items, record_undo=True):
        undo_data = []

        for index, in items:
            index = index if index < len(self.data) else len(self.data)-1
            removed = self.data.pop(index)
            undo_data.append((index, removed))

        if record_undo:
            self._record_undo("remove_row", undo_data)

    def _undo_remove_row(self, items):
        for index, row in reversed(items):
            self.data.insert(index, row[:])

    # --- Cell Methods ---

    def set_cell(self, items):
        items = [(row, col, new, self.data[row][col]) for row, col, new in items]
        self._set_cell(items)

    def _set_cell(self, items, record_undo=True):
        undo_data = []

        for row, col, new, old in items:
            self.data[row][col] = new
            undo_data.append((row, col, new, old))

        if record_undo:
            self._record_undo("set_cell", undo_data)

    def _undo_set_cell(self, items):
        undo_data = []

        for row, col, new, old in items:
            self.data[row][col] = old


    def get_cell(self, row, col):
        return self.data[row][col]

    # --- Reorder Methods ---

    def move_column(self, items):
        self._move_column(items)

    def _move_column(self, items, record_undo=True):
        undo_data = []

        for from_index, to_index in items:
            if from_index == to_index or not (0 <= from_index < len(self.column_names)) or not (0 <= to_index <= len(self.column_names)):
                continue

            name = self.column_names.pop(from_index)
            self.column_names.insert(to_index, name)
            # self.column_names.insert(to_index if from_index > to_index else to_index - 1, name)

            for row in self.data:
                cell = row.pop(from_index)
                row.insert(to_index, cell)
                # row.insert(to_index if from_index > to_index else to_index - 1, cell)

            undo_data.append((to_index, from_index))  # reverse move
            # undo_data.append((to_index if from_index > to_index else to_index - 1, from_index))  # reverse move

        if record_undo:
            self._record_undo("move_column", undo_data)

    def _undo_move_column(self, items):
        self._move_column(items, record_undo=False)

    def move_row(self, items):
        self._move_row(items)

    def _move_row(self, items, record_undo=True):
        undo_data = []

        for from_index, to_index in items:
            if from_index == to_index or not (0 <= from_index < len(self.data)) or not (0 <= to_index <= len(self.data)):
                continue

            row = self.data.pop(from_index)
            self.data.insert(to_index if from_index > to_index else to_index - 1, row)

            undo_data.append((to_index if from_index > to_index else to_index - 1, from_index))  # reverse move

        if record_undo:
            self._record_undo("move_row", undo_data)

    def _undo_move_row(self, items):
        self._move_row(items, record_undo=False)

    # --- Print Method ---

    def print(self, cell_width: int = 15):
        if not self.column_names:
            print("(Empty Table)")
            return

        def format_cell(content: str) -> str:
            return content[:cell_width].ljust(cell_width)

        def print_separator():
            print("*" + "*".join(["-" * cell_width for _ in self.column_names]) + "*")

        # Print header
        print_separator()
        header = "|" + "|".join([format_cell(name) for name in self.column_names]) + "|"
        print(header)
        print_separator()

        # Print rows
        for row in self.data:
            line = "|" + "|".join([format_cell(cell) for cell in row]) + "|"
            print(line)

        print_separator()

class Cacher:
    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        self.data = {}
        if os.path.isfile(self.file_path):
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __setitem__(self, key, value):
         self.data[key] = value
         with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

import random,string
class Tab:
    def __init__(self,tpy_file,tab_title):
        self.main_window = tpy_file.main_window
        self.project = tpy_file.project
        self.tpy_file = tpy_file
        self.tab_title = tab_title

        self.main_widget = QWidget()
        self.v_layout = QVBoxLayout(self.main_widget)
        self.v_layout.setContentsMargins(10, 10, 10, 10)
        self.v_layout.setSpacing(6)  # general spacing between elements

        # Tab title
        self.title_label = QLabel(self.tab_title)
        self.title_label.setStyleSheet(
            "font-weight: bold; border-radius: 6px; padding: 6px; border: 1px solid #ccc;"
        )
        self.v_layout.addWidget(self.title_label)

        # === Values table ===
        self.v_layout.addSpacerItem(QSpacerItem(0, 24))
        self.values_label = QLabel("Values")
        self.values_label.setStyleSheet("font-weight: bold;")
        self.v_layout.addWidget(self.values_label)

        self.values_table_view = CustomTableView(self,'vals')
        self.values_table_view.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        self.values_table_view.setMaximumHeight(72)
        self.v_layout.addSpacerItem(QSpacerItem(0, 12))
        self.v_layout.addWidget(self.values_table_view)

        # N = 200
        # self.values_table_view.model_.beginResetModel()

        # self.values_table_view.model_.table.insert_column([(i, f"Col{i}") for i in range(N)])
        # self.values_table_view.model_.table.insert_row([(0,)])

        # self.values_table_view.model_.endResetModel()

        # === Variables table ===
        self.v_layout.addSpacerItem(QSpacerItem(0, 24))
        self.variables_label = QLabel("Variables")
        self.variables_label.setStyleSheet("font-weight: bold;")
        self.v_layout.addWidget(self.variables_label)

        self.variables_table_view = CustomTableView(self,"vars")
        self.variables_table_view.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.v_layout.addWidget(self.variables_table_view)

        # self.variables_table_view.model_.beginResetModel()

        # self.variables_table_view.model_.table.insert_column([(i, f"Col{i}") for i in range(N)])
        # self.variables_table_view.model_.table.insert_row([(i,) for i in range(N)])

        # self.variables_table_view.model_.endResetModel()

        # cells = []
        # for row in range(N):
        #     for col in range(N):
        #         value = f"{row:0>3}-{col:0>3}"
        #         cells.append((row, col, value))
        # self.variables_table_view.model_.table.set_cell(cells)
        
        # model = self.variables_table_view.model_
        # topLeft = model.index(0, 0)
        # bottomRight = model.index(model.rowCount() - 1, model.columnCount() - 1)
        # model.dataChanged.emit(topLeft, bottomRight)

        # Add to tab widget
        self.main_window.tab_widget.addTab(self.main_widget, self.tab_title)
        self.main_window.tab_widget.setCurrentWidget(self.main_widget)

class TpyFile:
    def __init__(self,project,tpy_file_path):
        self.main_window = project.main_window
        self.project = project
        
        self.tpy_file_path = tpy_file_path
        self.tpy_file_name = os.path.basename(tpy_file_path)

        self.tab = Tab(self,self.tpy_file_name)

        self.create_time = os.path.getctime(tpy_file_path)
        self.mod_time = os.path.getmtime(tpy_file_path)

        self.writing = False

    def parse(self)

    def update(self):
        pass

class Project:
    def __init__(self,main_window):
        self.main_window = main_window
    
        self.project_cache = None
        self.project_path = None
        self.project_name = None
    
        self.tpy_files = {}

        self.directory_watcher = QFileSystemWatcher()
        self.directory_watcher.directoryChanged.connect(self.update)

        self.is_open = False

    def open(self, project_path):
        if self.is_open:
            self.close()

        self.project_path = project_path
        self.project_name = os.path.basename(project_path)
        self.project_cache = Cacher(os.path.join(project_path,".cache"))
        
        self.main_window.setWindowTitle(APPLICATION_NAME+' - '+self.project_name)

        for entry in sorted(os.listdir(project_path)):
            entry_path = os.path.join(project_path,entry)
            if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                self.tpy_files[entry] = TpyFile(self, entry_path)

        self.directory_watcher.addPath(self.project_path)

        self.is_open = True

    def close(self):
        if not self.is_open:
            return

        for tpy_file in self.tpy_files.values():
            tab = tpy_file.tab
            index = self.main_window.tab_widget.indexOf(tab.main_widget)
            if index != -1:
                self.main_window.tab_widget.removeTab(index)

        self.directory_watcher.removePath(self.project_path)

        self.tpy_files.clear()

        self.project_cache = None
        self.project_path = None
        self.project_name = None

        self.main_window.setWindowTitle(APPLICATION_NAME)

        self.is_open = False

    def update(self):
        for entry in sorted(os.listdir(self.project_path)):
            entry_path = os.path.join(self.project_path,entry)
            if entry in self.tpy_files:
                if os.path.getmtime(entry_path) > self.tpy_files[entry].mod_time:
                    if self.tpy_files[entry].writing:
                        self.tpy_files[entry].mod_time = os.path.getmtime(entry_path)
                        self.tpy_files[entry].writing = False
                    else:
                        self.tpy_files[entry].update()
            else:
                if os.path.isfile(entry_path) and entry.endswith('.tpy'):
                    self.tpy_files[entry] = TpyFile(self, entry_path)