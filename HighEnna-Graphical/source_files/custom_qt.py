from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from collections import defaultdict
from io import StringIO
import csv
import re

class CFooter(QLabel):
    _instances = set()  # keep track of all instances

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        CFooter._instances.add(self)

        self.setFont(QFont("Courier New"))

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clear)

        self._full_text = ""

    def __del__(self):
        CFooter._instances.discard(self)

    def clear(self):
        self._full_text = ""
        super().clear()

    def resizeEvent(self, event):
        self._update_elided_text()
        super().resizeEvent(event)

    def _update_elided_text(self):
        if not self._full_text:
            return
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width())
        super().setText(elided)

    def setText(self, text: str):
        self._full_text = text
        self._update_elided_text()

    @classmethod
    def broadcast(cls, message: str, time: int = 0):
        for footer in list(cls._instances):
            footer.setText(f" {message}")
            footer._timer.stop()
            if time > 0:
                footer._timer.start(time)

class CScrollBar(QScrollBar):
    def __init__(self,parent_widget=None):
        super().__init__()
        self.parent_widget=parent_widget

    def wheelEvent(self, event):
        self.parent_widget.wheelEvent(event)

class CScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setHorizontalScrollBar(CScrollBar(self))
        self.setVerticalScrollBar(CScrollBar(self))

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        if delta_x:
            scrollbar = self.horizontalScrollBar()
            delta = delta_x
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
            delta = delta_y
        else:
            scrollbar = self.verticalScrollBar()
            delta = delta_y

        if delta == 0:
            event.ignore()
            return

        delta = -(delta // 120) * scrollbar.singleStep() * 2
        new_value = scrollbar.value() + delta

        if new_value < scrollbar.minimum():
            if scrollbar.value() != scrollbar.minimum():
                scrollbar.setValue(scrollbar.minimum())
                event.accept()
            else:
                event.ignore()
        elif new_value > scrollbar.maximum():
            if scrollbar.value() != scrollbar.maximum():
                scrollbar.setValue(scrollbar.maximum())
                event.accept()
            else:
                event.ignore()
        else:
            scrollbar.setValue(new_value)
            event.accept()

class CTabBar(QTabBar):
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()

class CTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(CTabBar(self))

class CLabel(QLabel):
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.left_clicked.emit()
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            self.clicked.emit()
        else:
            super().mousePressEvent(event)

class CTableWidget(QTableWidget):
    def __init__(self, parent_window):
        super().__init__(0,0)
        self.parent_window = parent_window
        self.project = parent_window.parent().project

        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setHorizontalScrollBar(CScrollBar(self))
        self.setVerticalScrollBar(CScrollBar(self))

    def update_table(self):
        self.setRowCount(len(self.parent_window.receivers))
        self.setColumnCount(len(self.parent_window.assignees))
        self._init_headers()
        self._populate_checkboxes()
        self.model().dataChanged.emit(
                self.model().index(0, 0),
                self.model().index(self.rowCount()-1, self.columnCount()-1)
            )

    def _init_headers(self):
        self.receiver_map = {i:r for i,r in enumerate(sorted(self.parent_window.receivers))}
        self.receiver_map.update({r:i for i,r in self.receiver_map.items()})

        self.assignee_map = {i:a for i,a in enumerate(sorted(self.parent_window.assignees,key=lambda uuid: self.project.uuid_to_name[uuid]))}
        self.assignee_map.update({a:i for i,a in self.assignee_map.items()})

        font = QFont("Courier New")

        for receiver in self.parent_window.receivers:
            item = QTableWidgetItem(receiver)
            item.setFont(font)
            self.setVerticalHeaderItem(self.receiver_map[receiver], item)

        for module_uuid in self.parent_window.assignees:
            item = QTableWidgetItem(self.project.uuid_to_name[module_uuid])
            item.setFont(font)
            self.setHorizontalHeaderItem(self.assignee_map[module_uuid], item)

    def _populate_checkboxes(self):
        for receiver in self.parent_window.receivers:
            row = self.receiver_map[receiver]
            assigned_set = self.parent_window.relations[receiver]
            for module_uuid in self.parent_window.assignees:
                col = self.assignee_map[module_uuid]

                checkbox = QCheckBox()
                checkbox.setChecked(module_uuid in assigned_set)
                checkbox.stateChanged.connect(lambda state, r=receiver, m=module_uuid: self._on_checkbox_changed(r, m, state))
                
                widget = QWidget()
                hlayout = QHBoxLayout(widget)
                hlayout.addWidget(checkbox)
                hlayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hlayout.setContentsMargins(2, 2, 2, 2)

                self.setCellWidget(row, col, widget)

    def _on_checkbox_changed(self, receiver, module_uuid, state):
        if state == Qt.CheckState.Checked.value:
            self.parent_window.relations[receiver].add(module_uuid)
        else:
            self.parent_window.relations[receiver].discard(module_uuid)

    def toggle_selected_cells(self):
        selected = self.selectedIndexes()
        if not selected:
            return

        states = []
        for idx in selected:
            checkbox = self.cellWidget(idx.row(), idx.column()).layout().itemAt(0).widget()
            states.append(checkbox.isChecked())

        if any(states) and not all(states):
            new_state = True
        elif all(states):
            new_state = False
        else:
            new_state = True

        for idx in selected:
            checkbox = self.cellWidget(idx.row(), idx.column()).layout().itemAt(0).widget()
            checkbox.setChecked(new_state)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_selected_cells()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape and self.selectedIndexes():
            self.clearSelection()
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        if delta_x:
            scrollbar = self.horizontalScrollBar()
            delta = delta_x
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
            delta = delta_y
        else:
            scrollbar = self.verticalScrollBar()
            delta = delta_y

        if delta == 0:
            event.ignore()
            return

        delta = -(delta // 120) * scrollbar.singleStep() * 2
        new_value = scrollbar.value() + delta

        if new_value < scrollbar.minimum():
            if scrollbar.value() != scrollbar.minimum():
                scrollbar.setValue(scrollbar.minimum())
                event.accept()
            else:
                event.ignore()
        elif new_value > scrollbar.maximum():
            if scrollbar.value() != scrollbar.maximum():
                scrollbar.setValue(scrollbar.maximum())
                event.accept()
            else:
                event.ignore()
        else:
            scrollbar.setValue(new_value)
            event.accept()

    def sizeHint(self) -> QSize:
        total_width = self.verticalHeader().width()
        for col in range(self.columnCount()):
            total_width += self.columnWidth(col)

        total_height = self.horizontalHeader().height()
        for row in range(self.rowCount()):
            total_height += self.rowHeight(row)

        total_width += 2 * self.frameWidth() + 35
        total_height += 2 * self.frameWidth() + 5

        return QSize(total_width, total_height)

class CStyledItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.courier_new_font = QFont("Courier New")

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        palette = editor.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor('white'))
        editor.setPalette(palette)
        editor.setFont(self.courier_new_font)
        return editor

class CTableModel(QAbstractTableModel):
    def __init__(self, dictionary,data_table):
        super().__init__()
        self.dictionary = {'table_model':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.table = data_table

        self.courier_new_font = QFont("Courier New")

        self.siblings = [self]

    def couple_sibling(self,table_model):
        self.siblings.append(table_model)
        self.table.couple_sibling(table_model.table)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.FontRole:
            return self.courier_new_font
        elif role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
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
        return True

    def rowCount(self, parent=QModelIndex()):
        return len(self.table.data)

    def colCount(self, parent=QModelIndex()):
        return len(self.table.column_names)

    def columnCount(self, parent=QModelIndex()):
        return self.colCount(parent)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation != Qt.Orientation.Horizontal:
            return str(section+1)
        if 0 <= section < len(self.table.column_names):
            return self.table.column_names[section]
        return QVariant()

    def supportedDragActions(self):
        return Qt.DropAction.MoveAction

    def apply_table_action(self,table_action,*args):
        for table_model in self.siblings:
            table_model.beginResetModel()
        table_action(*args)
        for table_model in self.siblings:
            table_model.endResetModel()
            table_model.emit_data_change()

    def handle_column_move(self, from_index, to_index):
        if from_index == to_index:
            return
        self.apply_table_action(self.table.move_column,[(from_index, to_index)])

    def handle_row_move(self, from_index, to_index):
        if from_index == to_index:
            return
        self.apply_table_action(self.table.move_row,[(from_index, to_index)])

    def insert_column(self, items):
        self.apply_table_action(self.table.insert_column,items)

    def set_cell(self, items):
        self.apply_table_action(self.table.set_cell,items)

    def remove_column(self, items):
        self.apply_table_action(self.table.remove_column,items)

    def insert_row(self,items):
        self.apply_table_action(self.table.insert_row,items)

    def duplicate_row(self, items):
        self.apply_table_action(self.table.duplicate_row,items)

    def remove_row(self, items):
        self.apply_table_action(self.table.remove_row,items)

    def undo(self):
        self.apply_table_action(self.table.undo)

    def redo(self):
        self.apply_table_action(self.table.redo)

    def clear_cell(self,indices):
        self.apply_table_action(self.table.clear_cell,indices)

    def clear(self):
        self.apply_table_action(self.table.clear)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsEditable |
            Qt.ItemFlag.ItemIsDragEnabled |
            Qt.ItemFlag.ItemIsDropEnabled
        )

    def emit_data_change(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))


class CTableView(QTableView):
    def __init__(self, dictionary, data_table):
        super().__init__()

        self.dictionary = {'table_view':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.table_model = CTableModel(self.dictionary, data_table)
        self.setModel(self.table_model)

        self.setMouseTracking(True)

        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionsMovable(True)

        self.horizontalHeader().sectionMoved.connect(self.on_column_moved)
        self.verticalHeader().sectionMoved.connect(self.on_row_moved)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        self.setItemDelegate(CStyledItemDelegate())

        self.setHorizontalScrollBar(CScrollBar(self))
        self.setVerticalScrollBar(CScrollBar(self))

        self.createContextMenu = lambda self, position, index_at: None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            g_position = event.globalPosition()
            g_position =  QPoint(int(g_position.x()),int(g_position.y()))
            position = event.pos()
            position =  QPoint(int(position.x()),int(position.y()))
            self.createContextMenu(self, g_position,self.indexAt(position))
        else:
            return super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.table_model.undo()
                self.tpy_view.update_size_hint()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Y:
                self.table_model.redo()
                self.tpy_view.update_size_hint()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_C:
                self.copy_selection()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_V:
                self.paste_selection()
                event.accept()
                return
        elif event.key() == Qt.Key.Key_Delete:
            self.table_model.clear_cell([(index.row(),index.column()) for index in self.selectedIndexes()])
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            selected_indices = self.selectedIndexes()
            if len(selected_indices) == 1:
                self.edit(selected_indices[0])
                event.accept()
                return
        elif event.key() == Qt.Key.Key_Escape and self.selectedIndexes():
            self.clearSelection()
            event.accept()
        super().keyPressEvent(event)

    def couple_sibling(self,table_view):
        self.table_model.couple_sibling(table_view.table_model)

    def copy_selection(self):
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        rows = defaultdict(dict)
        for index in selected_indexes:
            rows[index.row()][index.column()] = index.data(Qt.ItemDataRole.DisplayRole)

        text_to_copy = ""
        for row in sorted(rows.keys()):
            row_data = []
            for col in sorted(rows[row].keys()):
                formated = rows[row][col].replace('"','""')
                row_data.append(f'"{formated}"')
            text_to_copy += "\t".join(row_data) + "\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)

    def paste_selection(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        reader = csv.reader(StringIO(text), delimiter='\t', quotechar='"')
        rows = [row for row in reader]

        if len(rows) == 1 and len(rows[0]) == 1:
            single_value = rows[0][0]
            cells_to_set = [(index.row(), index.column(), single_value) for index in selected_indexes]
            self.table_model.set_cell(cells_to_set)
            return

        start_index = self.currentIndex()
        if not start_index.isValid():
            return

        start_row = start_index.row()
        start_col = start_index.column()

        cells_to_set = []
        for i, columns in enumerate(rows):
            for j, value in enumerate(columns):
                target_row = start_row + i
                target_col = start_col + j
                model_index = self.table_model.index(target_row, target_col)
                if model_index.isValid():
                    cells_to_set.append((target_row, target_col, value))
        self.table_model.set_cell(cells_to_set)

    def on_column_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.table_model.handle_column_move(oldVisualIndex, newVisualIndex)

        header = self.horizontalHeader()
        header.blockSignals(True)
        for logical_index in range(header.count()):
            visual_index = header.visualIndex(logical_index)
            if visual_index != logical_index:
                header.moveSection(visual_index, logical_index)
        header.blockSignals(False)

    def on_row_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.table_model.handle_row_move(oldVisualIndex, newVisualIndex)

        header = self.verticalHeader()
        header.blockSignals(True)
        for logical_index in range(header.count()):
            visual_index = header.visualIndex(logical_index)
            if visual_index != logical_index:
                header.moveSection(visual_index, logical_index)
        header.blockSignals(False)

    def sizeHint(self):
        rows = min(self.table_model.rowCount(),15)

        total_row_height = sum(self.verticalHeader().sectionSize(row) for row in range(rows+1))
        header_height = self.horizontalHeader().height()
        padding = 15
        total_height = total_row_height + header_height + padding

        self.setMinimumHeight(total_height)
        return QSize(0, total_height)

    def event(self, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.grabMouse()
        elif event.type() == QEvent.Type.HoverLeave:
            self.releaseMouse()
        return super().event(event)

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        if delta_x:
            scrollbar = self.horizontalScrollBar()
            delta = delta_x
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
            delta = delta_y
        else:
            scrollbar = self.verticalScrollBar()
            delta = delta_y

        if delta == 0:
            event.ignore()
            return

        delta = -(delta // 120) * scrollbar.singleStep()
        new_value = scrollbar.value() + delta

        if new_value < scrollbar.minimum():
            if scrollbar.value() != scrollbar.minimum():
                scrollbar.setValue(scrollbar.minimum())
                event.accept()
            else:
                event.ignore()
        elif new_value > scrollbar.maximum():
            if scrollbar.value() != scrollbar.maximum():
                scrollbar.setValue(scrollbar.maximum())
                event.accept()
            else:
                event.ignore()
        else:
            scrollbar.setValue(new_value)
            event.accept()

class CErrorTableModel(QAbstractTableModel):
    def __init__(self, dictionary, data_table):
        super().__init__()
        self.dictionary = {'table_model': self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.table = data_table
        self.courier_new_font = QFont("Courier New")

    def rowCount(self, parent=QModelIndex()):
        return len(self.table.data)

    def colCount(self, parent=QModelIndex()):
        return len(self.table.column_names)

    def columnCount(self, parent=QModelIndex()):
        return self.colCount(parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            row = index.row()
            col = index.column()
            return self.table.get_cell(row, col)
        if role == Qt.ItemDataRole.FontRole:
            return self.courier_new_font
        if role == Qt.ItemDataRole.TextAlignmentRole:
            col_name = self.table.column_names[index.column()]

            left_cols = {"What","Line"}

            if col_name in left_cols:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            else:
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        return QVariant()

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled
        )

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation != Qt.Orientation.Horizontal:
            return str(section + 1)
        if 0 <= section < len(self.table.column_names):
            return self.table.column_names[section]
        return QVariant()

class DetailErrorWindow(QWidget):
    def __init__(self, parent, data):
        super().__init__(parent, flags=Qt.WindowType.Window)
        self.setWindowTitle(f"Error Details")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        content = QWidget()
        layout = QVBoxLayout(content)

        mono_font = QFont("Courier New")
        bold_font = QFont()
        bold_font.setBold(True)

        for key, value in data.items():
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setLineWidth(2)

            inner_layout = QVBoxLayout(frame)

            label_key = QLabel(f"{key}:")
            label_key.setFont(bold_font)

            label_value = QLabel(str(value))
            label_value.setFont(mono_font)
            label_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            if key in {"code", "line", "column"}:
                hlayout = QHBoxLayout()
                hlayout.addWidget(label_key)
                hlayout.addWidget(label_value)
                hlayout.addStretch()
                inner_layout.addLayout(hlayout)
            else:
                inner_layout.addWidget(label_key)
                inner_layout.addWidget(label_value)

            layout.addWidget(frame)

        layout.addStretch(1)

        # ---- Size management ----
        screen_geo = QGuiApplication.primaryScreen().availableGeometry()
        max_w = int(screen_geo.width() * 0.8)
        max_h = int(screen_geo.height() * 0.8)

        content.adjustSize()
        needed_size = content.sizeHint()

        if needed_size.width() > max_w or needed_size.height() > max_h:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(content)

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)
            self.resize(min(needed_size.width(), max_w),
                        min(needed_size.height(), max_h))
        else:
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(content)
            self.adjustSize()

        self.setFixedSize(self.size())

class CErrorTableView(QTableView):
    def __init__(self, dictionary, data_table):
        super().__init__()

        self.dictionary = {'table_view':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.data_table = data_table

        self.table_model = CErrorTableModel(self.dictionary,data_table)
        self.setModel(self.table_model)

        self.setMouseTracking(True)

        self.setSelectionMode(QTableView.SelectionMode.NoSelection)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        self.horizontalHeader().setSectionsMovable(False)
        self.verticalHeader().setSectionsMovable(False)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        self.setHorizontalScrollBar(CScrollBar(self))
        self.setVerticalScrollBar(CScrollBar(self))

        self.doubleClicked.connect(self.on_double_click)

    def on_double_click(self, index):
        if not index.isValid():
            return

        row = index.row()
        if row >= len(self.data_table):
            return

        data = {
            "code": self.data_table.get_cell(row, 0),
            "what": self.data_table.get_cell(row, 5),
            "line": self.data_table.get_cell(row, 2),
            "column": self.data_table.get_cell(row, 3),
            "content": self.data_table.get_cell(row, 4),
        }

        self.detail_window = DetailErrorWindow(self, data)
        self.detail_window.show()

    def sizeHint(self):
        rows = min(self.table_model.rowCount(),15)

        total_row_height = sum(self.verticalHeader().sectionSize(row) for row in range(rows+1))
        header_height = self.horizontalHeader().height()
        padding = 15
        total_height = total_row_height + header_height + padding

        self.setMinimumHeight(total_height)
        return QSize(0, total_height)

    def event(self, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.grabMouse()
        elif event.type() == QEvent.Type.HoverLeave:
            self.releaseMouse()
        return super().event(event)

    def wheelEvent(self, event):
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        if delta_x:
            scrollbar = self.horizontalScrollBar()
            delta = delta_x
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
            delta = delta_y
        else:
            scrollbar = self.verticalScrollBar()
            delta = delta_y

        if delta == 0:
            event.ignore()
            return

        delta = -(delta // 120) * scrollbar.singleStep()
        new_value = scrollbar.value() + delta

        if new_value < scrollbar.minimum():
            if scrollbar.value() != scrollbar.minimum():
                scrollbar.setValue(scrollbar.minimum())
                event.accept()
            else:
                event.ignore()
        elif new_value > scrollbar.maximum():
            if scrollbar.value() != scrollbar.maximum():
                scrollbar.setValue(scrollbar.maximum())
                event.accept()
            else:
                event.ignore()
        else:
            scrollbar.setValue(new_value)
            event.accept()

from time import time
class CFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.click_debouncer = QTimer(self)
        self.click_debouncer.setSingleShot(True)
        self.click_debouncer.timeout.connect(self.on_click_debouncer_timeout)

    def recursive_install_event_filter(self):
        def _recursive_install_event_filter(widget):
            widget.installEventFilter(self)
            for child in widget.children():
                if isinstance(child, QWidget):
                    _recursive_install_event_filter(child)
        _recursive_install_event_filter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            self.click_debouncer.start(5)
        return super().eventFilter(obj, event)

    def on_click_debouncer_timeout(self):
        self.clicked.emit()
