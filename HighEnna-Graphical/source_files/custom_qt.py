from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from collections import defaultdict
from io import StringIO
import csv

class CToolTip(QWidget):
    def __init__(self, parent, pos, text, duration=100):
        super().__init__(parent, flags=Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowOpacity(1.0)

        # self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: white;
                border-radius: 5px;
                padding: 5px 5px;
            }
        """)
        label.adjustSize()
        self.resize(label.size())

        # Position at given screen coordinates
        self.move(pos - QPoint(self.width() // 2, self.height() // 2))
        self.show()

        # Auto fade out after 'duration' milliseconds
        QTimer.singleShot(duration, self.fade_out)

    def fade_out(self):
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(800)  # Fade duration in ms
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.finished.connect(self.close)
        animation.start()

        # Keep reference to animation so it doesn't get garbage collected
        self._animation = animation

class CScrollArea(QScrollArea):
    def event(self, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.grabMouse()
        elif event.type() == QEvent.Type.HoverLeave:
            self.releaseMouse()
        return super().event(event)

    def wheelEvent(self, event: QWheelEvent):
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()

        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            bar = self.horizontalScrollBar()
            delta = delta_x if delta_x != 0 else delta_y
        else:
            bar = self.verticalScrollBar()
            delta = delta_y

        if delta == 0:
            event.ignore()
            return

        at_min = bar.value() == bar.minimum()
        print("at_min:",at_min)
        at_max = bar.value() == bar.maximum()
        print("at_max:",at_max)

        going_up = delta > 0
        print("going_up:",going_up)
        going_down = delta < 0
        print("going_down:",going_down)

        if (going_up and not at_min) or (going_down and not at_max):
            step = 10
            bar.setValue(bar.value() - delta / step)
            event.accept()

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
        self.delta_to_saved_version = 0

        self.courier_new_font = QFont("Courier New")

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
        self.delta_to_saved_version+=1
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

    def apply_table_action(self,table_action,*args,delta=1):
        self.beginResetModel()
        table_action(*args)
        self.endResetModel()
        self.delta_to_saved_version+=delta
        self.emit_data_change()

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
        self.apply_table_action(self.table.undo,delta=-1)

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

        self.setMouseTracking(True)
        
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionsMovable(True)

        self.table_model = CTableModel(self.dictionary, data_table)
        self.setModel(self.table_model)

        self.horizontalHeader().sectionMoved.connect(self.on_column_moved)
        self.verticalHeader().sectionMoved.connect(self.on_row_moved)
        
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        self.setItemDelegate(CStyledItemDelegate())

        self.siblings=[self]
        self.createContextMenu = lambda self, position, index_at: None

    def event(self, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.grabMouse()
        elif event.type() == QEvent.Type.HoverLeave:
            self.releaseMouse()
        return super().event(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
        else:
            scrollbar = self.verticalScrollBar()

        steps = event.angleDelta().y() // 120
        delta = -steps * scrollbar.singleStep()
        new_value = scrollbar.value() + delta

        # If scrollbar can still move, handle normally
        if scrollbar.minimum() <= new_value <= scrollbar.maximum():
            scrollbar.setValue(new_value)
        else:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                scrollbar = self.main_window.scroll_area.horizontalScrollBar()
            else:
                scrollbar = self.main_window.scroll_area.verticalScrollBar()
            
            delta = -steps * scrollbar.singleStep()
            new_value = scrollbar.value() + delta*3
            scrollbar.setValue(max(scrollbar.minimum(), min(new_value, scrollbar.maximum())))

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
        super().keyPressEvent(event)

    def copy_selection(self):
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return

        # Create a 2D array of selected values
        rows = defaultdict(dict)
        for index in selected_indexes:
            rows[index.row()][index.column()] = index.data(Qt.ItemDataRole.DisplayRole)

        # Convert to a string with tab-separated values for each row and newlines between rows
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

    def installEventFilter(self,obj):
        super().installEventFilter(obj)
        self.viewport().installEventFilter(obj)
        self.horizontalHeader().installEventFilter(obj)
        self.verticalHeader().installEventFilter(obj)
    
    def sizeHint(self):
        rows = self.table_model.rowCount()
        total_row_height = sum(self.verticalHeader().sectionSize(row) for row in range(rows+1))
        header_height = self.horizontalHeader().height()
        padding = 15
        total_height = total_row_height + header_height + padding
        self.setMinimumHeight(total_height)
        return QSize(0, total_height)

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

        # Build the content widget
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

            # key label
            label_key = QLabel(f"{key}:")
            label_key.setFont(bold_font)

            # value label
            label_value = QLabel(str(value))
            label_value.setFont(mono_font)
            label_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            if key in {"code", "line", "column"}:
                # place key and value side by side
                hlayout = QHBoxLayout()
                hlayout.addWidget(label_key)
                hlayout.addWidget(label_value)
                hlayout.addStretch()
                inner_layout.addLayout(hlayout)
            else:
                # stack key and value vertically
                inner_layout.addWidget(label_key)
                inner_layout.addWidget(label_value)

            layout.addWidget(frame)

        # Add spacing/stretch so it looks clean
        layout.addStretch(1)

        # ---- Size management ----
        screen_geo = QGuiApplication.primaryScreen().availableGeometry()
        max_w = int(screen_geo.width() * 0.8)
        max_h = int(screen_geo.height() * 0.8)

        content.adjustSize()
        needed_size = content.sizeHint()

        if needed_size.width() > max_w or needed_size.height() > max_h:
            # Wrap content in scroll area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(content)

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)
            self.resize(min(needed_size.width(), max_w),
                        min(needed_size.height(), max_h))
        else:
            # No scroll needed
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(content)
            self.adjustSize()

        # Disable resizing
        self.setFixedSize(self.size())

class CErrorTableView(QTableView):
    def __init__(self, dictionary, data_table):
        super().__init__()

        self.dictionary = {'table_view':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.data_table = data_table
        self.setMouseTracking(True)
        
        self.horizontalHeader().setSectionsMovable(False)
        self.verticalHeader().setSectionsMovable(False)

        self.table_model = CErrorTableModel(self.dictionary,data_table)
        self.setModel(self.table_model)

        self.doubleClicked.connect(self.on_double_click)
        
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
        else:
            scrollbar = self.verticalScrollBar()

        steps = event.angleDelta().y() // 120
        delta = -steps * scrollbar.singleStep()
        new_value = scrollbar.value() + delta

        # If scrollbar can still move, handle normally
        if scrollbar.minimum() <= new_value <= scrollbar.maximum():
            scrollbar.setValue(new_value)
        else:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                scrollbar = self.main_window.scroll_area.horizontalScrollBar()
            else:
                scrollbar = self.main_window.scroll_area.verticalScrollBar()
            
            delta = -steps * scrollbar.singleStep()
            new_value = scrollbar.value() + delta*3
            scrollbar.setValue(max(scrollbar.minimum(), min(new_value, scrollbar.maximum())))

    def on_double_click(self, index):
        if not index.isValid():
            return

        row = index.row()
        if row >= len(self.data_table):
            return

        # Gather data into dict
        data = {
            "code": self.data_table.get_cell(row, 0),
            "what": self.data_table.get_cell(row, 5),
            "line": self.data_table.get_cell(row, 2),
            "column": self.data_table.get_cell(row, 3),
            "content": self.data_table.get_cell(row, 4),
        }

        # Create child window (owned by self)
        self.detail_window = DetailErrorWindow(self, data)
        self.detail_window.show()

    def installEventFilter(self,obj):
        super().installEventFilter(obj)
        self.viewport().installEventFilter(obj)
        # self.horizontalHeader().installEventFilter(obj)
        # self.verticalHeader().installEventFilter(obj)

    def sizeHint(self):
        rows = self.table_model.rowCount()
        total_row_height = sum(self.verticalHeader().sectionSize(row) for row in range(rows+1))
        header_height = self.horizontalHeader().height()
        padding = 15
        total_height = total_row_height + header_height + padding
        self.setMinimumHeight(total_height)
        return QSize(0, total_height)

from time import time
class CFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)

        self.click_debouncer = QTimer(self)
        self.click_debouncer.setSingleShot(True)
        self.click_debouncer.timeout.connect(self.on_click_debouncer_timeout)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            self.click_debouncer.start(5)
        return super().eventFilter(obj, event)

    def on_click_debouncer_timeout(self):
        self.clicked.emit()
