from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class CScrollArea(QScrollArea):
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            delta = event.angleDelta().y()
            scroll_step = 10
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta / scroll_step)
            event.accept()
        else:
            delta = event.angleDelta().y()
            scroll_step = 10
            new_value = self.verticalScrollBar().value() - delta / scroll_step
            self.verticalScrollBar().setValue(int(new_value))
            event.accept()
            super().wheelEvent(event)

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

class CTableModel(QAbstractTableModel):
    def __init__(self, dictionary,data_table):
        super().__init__()
        self.dictionary = {'table_model':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.table = data_table

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
        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row = index.row()
        col = index.column()
        self.table.set_cell([(row, col, str(value))])
        self.dataChanged.emit(index, index, [role])
        # self.table.print()
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
            return str(section+1)
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

    def on_column_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        if self.model():
            self.model().handle_column_move(oldVisualIndex, newVisualIndex)

            header = self.horizontalHeader()
            header.blockSignals(True)
            for logical_index in range(header.count()):
                visual_index = header.visualIndex(logical_index)
                if visual_index != logical_index:
                    header.moveSection(visual_index, logical_index)
            header.blockSignals(False)

            # self.table_model.table.print()

    def on_row_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        if self.model():
            self.model().handle_row_move(oldVisualIndex, newVisualIndex)

            header = self.verticalHeader()
            header.blockSignals(True)
            for logical_index in range(header.count()):
                visual_index = header.visualIndex(logical_index)
                if visual_index != logical_index:
                    header.moveSection(visual_index, logical_index)
            header.blockSignals(False)

            # self.table_model.table.print()
    
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
        self.fixed_font = QFont("Courier New")

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
            return self.fixed_font
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

            if key in {"code", "row", "col"}:
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

    # def on_double_click(self, index):
    #     if not index.isValid(): return
    #     row = index.row()
    #     if row >= len(self.data_table): return
    #     code = self.data_table.get_cell(row,0)
    #     message = get_error_message(code)
    #     msg_box = QMessageBox(self)
    #     msg_box.setIcon(QMessageBox.Icon.NoIcon)
    #     msg_box.setWindowTitle(f"Error {code}")
    #     msg_box.setText(message)
    #     msg_box.show()

    def on_double_click(self, index):
        if not index.isValid():
            return

        row = index.row()
        if row >= len(self.data_table):
            return

        # Gather data into dict
        data = {
            "code": self.data_table.get_cell(row, 0),
            "row": self.data_table.get_cell(row, 1),
            "col": self.data_table.get_cell(row, 2),
            "line": self.data_table.get_cell(row, 3),
            "what": self.data_table.get_cell(row, 4),
        }

        # Create child window (owned by self)
        self.detail_window = DetailErrorWindow(self, data)
        self.detail_window.show()

    def sizeHint(self):
        rows = self.table_model.rowCount()
        total_row_height = sum(self.verticalHeader().sectionSize(row) for row in range(rows+1))
        header_height = self.horizontalHeader().height()
        padding = 15
        total_height = total_row_height + header_height + padding
        self.setMinimumHeight(total_height)
        return QSize(0, total_height)