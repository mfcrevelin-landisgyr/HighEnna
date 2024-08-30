from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from tplbackend import TplProject

from appdirs import user_cache_dir
from collections import deque
from time import sleep
import hashlib
import json
import sys
import os

#https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def set_dark_theme(self):
    with open(resource_path("assets\\dark_theme.json"), 'r') as json_file:
        parameters = json.load(json_file)

    palette = self.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(parameters["Window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(parameters["WindowText"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(parameters["Base"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(parameters["AlternateBase"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(parameters["ToolTipBase"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(parameters["ToolTipText"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(parameters["Text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(parameters["Button"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(parameters["ButtonText"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(parameters["BrightText"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(parameters["Link"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(parameters["Highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(parameters["HighlightedText"]))
    self.setPalette(palette)

application_name = "High Enna"

class Cacher:
    def __init__(self, app_name):

        sanitized_app_name = []
        for char in app_name.strip().lower():
            if char.isalnum():
                sanitized_app_name.append(char)
            else:
                sanitized_app_name.append('_')
        
        self.app_name =  ''.join(sanitized_app_name)

        self.cache_dir = os.path.join(user_cache_dir(app_name), '')
        self.path = os.path.join(self.cache_dir,f"{self.app_name}.json")
        
        os.makedirs(self.cache_dir, exist_ok=True)

        self.data = {}
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                self.data = json.load(f)

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __setitem__(self, key, value):
         self.data[key] = value
         with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=1)

cacher = Cacher(application_name)

class ProgressBarWindow(QMainWindow):
    def __init__(self, parent, tpl_project):
        super().__init__(parent)
        self.parent = parent
        
        self.tpl_project = tpl_project
        
        self.setWindowTitle(application_name + " - Progress Window")
        self.setFixedSize(400, 55)

        # Set up the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Create a timer to update the progress bar
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)

        set_dark_theme(self)

        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)

    def update_progress(self):
        total = self.tpl_project.total()
        current = self.tpl_project.current()
        is_finished = self.tpl_project.is_finished()
        
        if total > 0:
            progress = int((float(current) / float(total)) * 100.0)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"Rendering: {progress}%")
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Waiting for data...")


class TplLogMessageBox(QMainWindow):
    def __init__(self, parent, tpl_index):
        super().__init__(parent)

        self.message = parent.tpl_project.log(tpl_index)
        self.name = parent.tpl_project.name(tpl_index)
        if not cacher[f"TplLogMessageBox:default_save_dir:{self.name}"]:
            cacher[f"TplLogMessageBox:default_save_dir:{self.name}"] = os.path.dirname(parent.tpl_project.path(tpl_index))

        lines = self.message.splitlines()

        max_h = len(lines)
        max_w = 0
        for line in lines:
            max_w = max(max_w,len(line))
        max_w+=2

        self.file_watcher = QFileSystemWatcher([parent.tpl_project.path(tpl_index)])
        self.file_watcher.fileChanged.connect(self.close)

        self.setWindowTitle(application_name + f" - Log {self.name}")
        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))

        f_size = 11
        self.scale = f_size/9

        self.scroll_area_width  = min(1280, int(7*max_w*self.scale)+50)
        self.scroll_area_height = min(600 ,int(14*max_h*self.scale)+35)
        
        layout = QVBoxLayout()

        central_widget = QWidget()

        self.label = QLabel(self.message)
        self.label.setWordWrap(True)
        self.label.setFont(QFont('Courier New',f_size))
        
        scroll_layout = QHBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setFixedSize(self.scroll_area_width, self.scroll_area_height)

        scroll_layout.addWidget(self.scroll_area)
        layout.addLayout(scroll_layout)
        
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(100)
        ok_button.clicked.connect(self.close)
        
        write_button = QPushButton("Write to file")
        write_button.setFixedWidth(100)
        write_button.clicked.connect(self.write_button_clicked)
        
        button_layout.addWidget(ok_button)
        button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        button_layout.addWidget(write_button)
        
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        size_hint = self.sizeHint()

        self.screen_geometry = QGuiApplication.primaryScreen().geometry()
        total_width = min(size_hint.width(),self.screen_geometry.width())
        total_height = min(size_hint.height(),self.screen_geometry.height()-100)

        self.setFixedWidth(total_width)
        self.setFixedHeight(total_height)

        set_dark_theme(self)

    def write_button_clicked(self):
        try:
            default_dir = cacher[f"TplLogMessageBox:default_save_dir:{self.name}"]
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_dir, "Log Files (*.log)")
            if file_path:
                cacher[f"TplLogMessageBox:default_save_dir:{self.name}"] = os.path.dirname(file_path)
                with open(file_path, "w") as f:
                    f.write(self.message)
                self.close()
        except Exception as e:
            QMessageBox.critical(self,"",traceback.format_exc())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class ModuleListWindow(QMainWindow):
    def __init__(self,parent,tpl_project, tpl_index=None):
        super().__init__(parent)

        self.parent = parent
        self.tpl_project = tpl_project
        self.tpl_index = tpl_index

        if self.tpl_index is None:
            self.setWindowTitle(application_name + " - Module Manager")
        else:
            self.setWindowTitle(application_name + " - Module Manager - " + self.tpl_project.name(self.tpl_index))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(button_layout)

        self.add_module_button = QPushButton("Import Module")
        self.add_module_button.clicked.connect(self.add_module)
        self.add_module_button.setFixedWidth(150)
        button_layout.addWidget(self.add_module_button)

        self.add_from_module_button = QPushButton("Import From Module")
        self.add_from_module_button.clicked.connect(self.add_from_module)
        self.add_from_module_button.setFixedWidth(150)
        button_layout.addWidget(self.add_from_module_button)

        self.add_file_button = QPushButton("Import File")
        self.add_file_button.clicked.connect(self.add_file)
        self.add_file_button.setFixedWidth(150)
        button_layout.addWidget(self.add_file_button)

        button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.remove_button = QPushButton("Remove Import")
        self.remove_button.clicked.connect(self.remove_selected)
        self.remove_button.setFixedWidth(150)
        button_layout.addWidget(self.remove_button)

        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.printt)
        self.print_button.setFixedWidth(150)
        button_layout.addWidget(self.print_button)

        self.org_imported_modules = set()
        self.org_imported_from_modules = set()
        self.org_imported_file_modules = set()

        self.add_imported_modules = set()
        self.add_imported_from_modules = set()
        self.add_imported_file_modules = set()

        self.rmv_imported_modules = set()
        self.rmv_imported_from_modules = set()
        self.rmv_imported_file_modules = set()

        
        self.item_to_set = dict()

        if self.tpl_index is None:
            for tpl_index in range(len(self.tpl_project)):
                self.org_imported_modules = self.org_imported_modules.union(self.tpl_project.get_modules(tpl_index))
                self.org_imported_from_modules = self.org_imported_from_modules.union(self.tpl_project.get_from_modules(tpl_index))
                self.org_imported_file_modules = self.org_imported_file_modules.union(self.tpl_project.get_file_modules(tpl_index))
        else:
            self.org_imported_modules = self.org_imported_modules.union(self.tpl_project.get_modules(self.tpl_index))
            self.org_imported_from_modules = self.org_imported_from_modules.union(self.tpl_project.get_from_modules(self.tpl_index))
            self.org_imported_file_modules = self.org_imported_file_modules.union(self.tpl_project.get_file_modules(self.tpl_index))

        
        for module_name in self.org_imported_modules:
            item = f"import {module_name}"
            self.list_widget.addItem(item)
            self.item_to_set[item] = ("imported_modules",module_name)
        
        for module_name,attribute in self.org_imported_from_modules:
            item = f"from {module_name} import {attribute}"
            self.list_widget.addItem(item)
            self.item_to_set[item] = ("imported_from_modules",(module_name,attribute))
        
        for file_name,file_content in self.org_imported_file_modules:
            item = f"File: {file_name}"
            self.list_widget.addItem(item)
            self.item_to_set[item] = ("imported_file_modules",(file_name,file_content))

        set_dark_theme(self)
        self.screen_geometry = QGuiApplication.primaryScreen().geometry()

    def adjust_size(self):
        total_width = self.list_widget.sizeHintForColumn(0) + 20
        total_height = self.list_widget.sizeHintForRow(0) * self.list_widget.count() + 20

        total_width = max(total_width,self.width())
        total_height = max(total_height,self.height())

        total_width = min(total_width,self.screen_geometry.width())
        total_height = min(total_height,self.screen_geometry.height()-100)

        self.resize(total_width, total_height)


    def printt(self):
        modules = []
        from_modules = []
        files = []
        for t,c in self.items:
            if (t=='m'):
                modules.append(c)
            elif (t=='fm'):
                from_modules.append(c)
            elif (t=='f'):
                files.append(c)

        print("Modules:")
        for i in modules:
            print(f"\t{i}")
        print("From Modules:")
        for i in from_modules:
            print(f"\t{i}")
        print("Files:")
        for i in files:
            print(f"\t{i[0]}:{i[1][:20]}")

    def add_module(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(application_name + " - Import Module")

        layout = QFormLayout(dialog)
        module_input = QLineEdit()
        module_input.setPlaceholderText("module")
        layout.addRow("Module:", module_input)

        button_box = QPushButton("Import", dialog)
        button_box.clicked.connect(lambda: self.accept_module(dialog, module_input.text()))
        layout.addWidget(button_box)

        dialog.exec()

    def accept_module(self, dialog, module_name):
        module_name = module_name.strip()
        if module_name:
            if module_name in self.org_imported_modules:
                if module_name in self.rmv_imported_modules:
                    self.rmv_imported_modules.remove(module_name)
                    item = f"import {module_name}"
                    self.list_widget.addItem(item)
            else:
                self.add_imported_modules.add(module_name)
                item = f"import {module_name}"
                self.item_to_set[item] = ("imported_modules",(module_name,))
                self.list_widget.addItem(item)
        dialog.accept()
        self.adjust_size()

    def add_from_module(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(application_name + " - Import From Module")

        layout = QFormLayout(dialog)
        module_input = QLineEdit()
        module_input.setPlaceholderText("module")
        attribute_input = QLineEdit()
        attribute_input.setPlaceholderText("attribute")
        layout.addRow("Module:", module_input)
        layout.addRow("Attribute:", attribute_input)

        button_box = QPushButton("Import", dialog)
        button_box.clicked.connect(lambda: self.accept_from_module(dialog, module_input.text(), attribute_input.text()))
        layout.addWidget(button_box)

        dialog.exec()

    def accept_from_module(self, dialog, module_name, attribute):
        module_name = module_name.strip()
        attribute = attribute.strip()
        if module_name and attribute:
            if (module_name,attribute) in self.org_imported_from_modules:
                if (module_name,attribute) in self.rmv_imported_from_modules:
                    self.rmv_imported_from_modules.remove((module_name,attribute))
                    item = f"from {module_name} import {attribute}"
                    self.list_widget.addItem(item)
            else:
                self.add_imported_from_modules.add((module_name,attribute))
                item = f"from {module_name} import {attribute}"
                self.item_to_set[item] = ("imported_from_modules",(module_name,attribute))
                self.list_widget.addItem(item)
        dialog.accept()
        self.adjust_size()

    def add_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Python Files (*.py)")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            for file_path in file_paths:
                with open(file_path, 'r') as file:
                    file_content = file.read()
                file_name = os.path.basename(file_path)

                org_contents = [c for n,c in self.org_imported_file_modules]
                rmv_contents = [c for n,c in self.rmv_imported_file_modules]

                if file_content in org_contents:
                    if file_content in rmv_contents:
                        self.rmv_imported_file_modules = set((n,c) for n,c in self.rmv_imported_file_modules if not c == file_content)
                        item = f"File: {file_name}"
                        self.list_widget.addItem(item)
                else:
                    self.add_imported_file_modules.add((file_name,file_content))
                    item = f"File: {file_name}"
                    self.item_to_set[item] = ("imported_file_modules",(file_name,file_content))
                    self.list_widget.addItem(item)
        self.adjust_size()

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()

        indices_to_remove = [self.list_widget.row(item) for item in selected_items]
        for index in sorted(indices_to_remove, reverse=True):
            self.list_widget.takeItem(index)

        for item in selected_items:
            item = item.text()
            item_type,item_params = self.item_to_set[item]
            if item_type == "imported_modules":
                module_name = item_params
                if module_name in self.org_imported_modules:
                    self.rmv_imported_modules.add(module_name)
                else:
                    if module_name in self.add_imported_modules:
                        self.add_imported_modules.remove(module_name)
            if item_type == "imported_from_modules":
                module_name, attribute = item_params
                if (module_name,attribute) in self.org_imported_from_modules:
                    self.rmv_imported_from_modules.add((module_name,attribute))
                else:
                    if (module_name,attribute) in self.add_imported_from_modules:
                        self.add_imported_from_modules.remove((module_name,attribute))
            if item_type == "imported_file_modules":
                org_contents = [c for n,c in self.org_imported_file_modules]
                add_contents = [c for n,c in self.add_imported_file_modules]
                file_name, file_content = item_params
                if file_content in org_contents:
                    self.rmv_imported_file_modules.add((file_name,file_content))
                else:
                    if file_content in add_contents:
                        self.add_imported_file_modules = set((n,c) for n,c in self.add_imported_file_modules if not c == file_content)

    def closeEvent(self, event):
        if self.tpl_index is None:
            for tpl_index in range(len(self.tpl_project)):
                self.tpl_project.update_modules(tpl_index,self.add_imported_modules,self.rmv_imported_modules)
                self.tpl_project.update_from_modules(tpl_index,self.add_imported_from_modules,self.rmv_imported_from_modules)
                self.tpl_project.update_file_modules(tpl_index,self.add_imported_file_modules,self.rmv_imported_file_modules)
        else:
            self.tpl_project.update_modules(self.tpl_index,self.add_imported_modules,self.rmv_imported_modules)
            self.tpl_project.update_from_modules(self.tpl_index,self.add_imported_from_modules,self.rmv_imported_from_modules)
            self.tpl_project.update_file_modules(self.tpl_index,self.add_imported_file_modules,self.rmv_imported_file_modules)
        self.tpl_project.save_modules()
        event.accept()

class TplModel(QAbstractTableModel):
    def __init__(self,parent,tpl_project, tpl_index):
        super().__init__(parent)
        self.parent = parent
        self.tpl_project = tpl_project
        self.tpl_index = tpl_index

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):
            return self.tpl_project.get_cell(self.tpl_index,index.row(), index.column())

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not role == Qt.ItemDataRole.EditRole:
            return False
        
        self.tpl_project.set_cell(self.tpl_index,index.row(), index.column(),str(value))
        self.emit_data_change()
        return True

    def undo(self):
        self.beginResetModel()
        self.tpl_project.undo(self.tpl_index)
        self.endResetModel()
        self.emit_data_change()

    def redo(self):
        self.beginResetModel()
        self.tpl_project.redo(self.tpl_index)
        self.endResetModel()
        self.emit_data_change()

    def clear(self,indices):
        formated_indices = [(i.row(),i.column()) for i in indices]
        self.beginResetModel()
        self.tpl_project.clear_dataframe_indices(self.tpl_index,formated_indices)
        self.endResetModel()
        self.emit_data_change()

    def save_data(self):
        self.tpl_project.save_data(self.tpl_index)

    def rowCount(self, parent=QModelIndex()):
        return self.tpl_project.row_count(self.tpl_index)

    def columnCount(self, parent=QModelIndex()):
        return self.tpl_project.col_count(self.tpl_index)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                l = self.tpl_project.vars(self.tpl_index)
                if (section >= len(l)):
                    return ""
                return self.tpl_project.vars(self.tpl_index)[section]
            else:
                return str(section + 1)

    def insertRows(self, rows):
        self.beginResetModel()
        if isinstance(rows,int) or self.rowCount():
            self.tpl_project.insert_rows(self.tpl_index,rows)
        else:
            self.tpl_project.insert_rows(self.tpl_index,len(rows))
        self.endResetModel()
        self.emit_data_change()

    def removeRows(self, rows):
        self.beginResetModel()
        self.tpl_project.remove_rows(self.tpl_index,rows)
        self.endResetModel()
        self.emit_data_change()

    def duplicateRows(self, rows):
        self.beginResetModel()
        self.tpl_project.duplicate_rows(self.tpl_index,rows)
        self.endResetModel()
        self.emit_data_change()

    def emit_data_change(self):
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
        self.parent.parent.adjust_size()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

class PopupMessage(QDialog):

    def __init__(self, parent, message):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Popup Message")
        
        title = application_name+" - Popup"

        self.setWindowTitle(title)

        layout = QVBoxLayout()
        
        message_label_layout = QHBoxLayout()
        message_label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label_layout.addWidget(message_label)
        
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(message_label_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

        self.setMinimumSize(200, 80)

        set_dark_theme(self)

class TplTableView(QTableView):

    def __init__(self,parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMouseTracking(True)
        self.editing = False

    def event(self, event):
        if event.type() == QEvent.Type.HoverEnter:
            self.grabMouse()
        elif event.type() == QEvent.Type.HoverLeave:
            self.releaseMouse()
        return super().event(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            g_position = event.globalPosition()
            g_position =  QPoint(int(g_position.x()),int(g_position.y()))
            position = event.pos()
            position =  QPoint(int(position.x()),int(position.y()))
            self.createContextMenu(g_position,self.indexAt(position))
        else:
            return super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_S:
                self.model().save_data()
                event.accept()
                window = PopupMessage(self,"Dataframe saved.")
                window.show()
                return
            elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                self.parent.render_all_push_button_on_clicked()
                return
            elif event.key() == Qt.Key.Key_Z:
                self.model().undo()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Y:
                self.model().redo()
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
            self.model().clear(self.selectedIndexes())
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.model().clear(self.selectedIndexes())
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            selected_indices = self.selectedIndexes()
            if len(selected_indices) == 1:
                self.edit(selected_indices[0])
                event.accept()
                return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            delta = event.angleDelta().y()
            scroll_step = 120
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta / scroll_step)
            event.accept()
        else:
            super().wheelEvent(event)

    def setModel(self, model):
        super().setModel(model)
        model.dataChanged.connect(self.fit_to_dataframe)
        self.fit_to_dataframe()

    def fit_to_dataframe(self):
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        total_height = 45
        for row in range(self.model().rowCount()):
            total_height += self.rowHeight(row)

        self.setFixedHeight(total_height)

    def sizeHint(self):

        total_width = 45
        for column in range(self.model().columnCount()):
            total_width += self.columnWidth(column)

        total_height = 45
        for row in range(self.model().rowCount()):
            total_height += self.rowHeight(row)

        total_width  += self.horizontalHeader().sizeHint().height()
        total_height += self.verticalHeader().sizeHint().height()

        return QSize(total_width, total_height)

    def createContextMenu(self, position, index_at):
        menu = QMenu()
        set_dark_theme(menu)

        selected_indices = self.selectedIndexes()
        rows = list({idx.row() for idx in selected_indices})

        if not any(index_at.row() == idx.row() for idx in selected_indices):
            self.selectionModel().clearSelection()
            rows = [index_at.row()]

        if len(rows)>1:
            render_action = menu.addAction("Render scripts")
            delete_action = menu.addAction("Delete Rows")
            duplicate_action = menu.addAction("Duplicate rows")

            row_above_action = (None,None) # action may return as None...
            row_below_action = (None,None) 
        else:
            render_action = menu.addAction("Render script")
            delete_action = menu.addAction("Delete Row")
            duplicate_action = menu.addAction("Duplicate row")

            row_above_action = menu.addAction("Insert Row Above")
            row_below_action = menu.addAction("Insert Row Below")

        n_rows_action = menu.addAction("Add N Rows")

        action = menu.exec(position)
        rows = list(rows)
        if action == row_above_action:
            self.model().insertRows(rows)
        elif action == row_below_action:
            for i in range(len(rows)):
                rows[i] += 1
            self.model().insertRows(rows)
        elif action == n_rows_action:
            num, ok = QInputDialog.getInt(self, "Insert N Rows Above", "Number of rows:", 1, 1)
            if ok:
                self.model().insertRows(num)
        elif action == delete_action:
            self.model().removeRows(rows)
        elif action == duplicate_action:
            self.model().duplicateRows(rows)
        elif action == render_action:
            self.parent.tpl_project.render(self.model().tpl_index, rows)
            window = ProgressBarWindow(self.parent, self.parent.tpl_project)
            window.show()
            self.parent.color_tpl_names_on_scroll_list_labels()

    def copy_selection(self):
            selected_indexes = self.selectedIndexes()
            if not selected_indexes:
                return
            
            # Sort selected indexes by row and column
            selected_indexes.sort(key=lambda x: (x.row(), x.column()))

            # Create a 2D array of selected values
            rows = {}
            for index in selected_indexes:
                if index.row() not in rows:
                    rows[index.row()] = {}
                rows[index.row()][index.column()] = index.data(Qt.ItemDataRole.DisplayRole)
            
            # Convert to a string with tab-separated values for each row and newlines between rows
            text_to_copy = ""
            for row in sorted(rows.keys()):
                row_data = []
                for col in sorted(rows[row].keys()):
                    row_data.append(rows[row][col])
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

        # Check if only one value is copied
        rows = text.split("\n")[:-1]
        if len(rows) == 1 and len(rows[0].split("\t")) == 1:
            single_value = rows[0]
            cells_to_set = [(index.row(), index.column(), single_value) for index in selected_indexes]
            self.model().tpl_project.set_cells(self.model().tpl_index, cells_to_set)
            self.model().emit_data_change()
            return

        # If there are multiple values, paste as usual starting from the current index
        start_index = self.currentIndex()
        if not start_index.isValid():
            return

        start_row = start_index.row()
        start_col = start_index.column()

        cells_to_set = []
        for i, row in enumerate(rows):
            columns = row.split("\t")
            for j, column in enumerate(columns):
                target_row = start_row + i
                target_col = start_col + j
                model_index = self.model().index(target_row, target_col)
                if model_index.isValid():
                    cells_to_set.append((target_row, target_col, column))
        self.model().tpl_project.set_cells(self.model().tpl_index, cells_to_set)
        self.model().emit_data_change()

class CustomScrollArea(QScrollArea):
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

class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
    def mousePressEvent(self, event):
        self.clicked.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(application_name)
        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))

        self.directory_path = ""
        self.output_directory_path = ""

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        directory_h_layout_widget = QWidget()
        directory_h_layout = QHBoxLayout(directory_h_layout_widget)
        directory_h_layout.setSpacing(5)
        directory_h_layout.setContentsMargins(1, 1, 1, 1)


        self.directory_line_edit = QLineEdit()
        self.directory_line_edit.returnPressed.connect(self.directory_line_edit_on_return_pressed)
        self.directory_line_edit.setPlaceholderText("Project directory")
        directory_h_layout.addWidget(self.directory_line_edit)

        self.directory_push_button = QPushButton("Browse")
        self.directory_push_button.setFixedSize(100, 25)
        self.directory_push_button.clicked.connect(self.directory_push_button_on_clicked)
        directory_h_layout.addWidget(self.directory_push_button)

        self.layout.addWidget(directory_h_layout_widget)

        output_directory_h_layout_widget = QWidget()
        output_directory_h_layout = QHBoxLayout(output_directory_h_layout_widget)
        output_directory_h_layout.setSpacing(5)
        output_directory_h_layout.setContentsMargins(1, 1, 1, 1)

        self.output_directory_line_edit = QLineEdit()
        self.output_directory_line_edit.returnPressed.connect(self.output_directory_line_edit_on_return_pressed)
        self.output_directory_line_edit.setPlaceholderText("Output directory")
        output_directory_h_layout.addWidget(self.output_directory_line_edit)

        self.output_directory_push_button = QPushButton("Browse")
        self.output_directory_push_button.setFixedSize(100, 25)
        self.output_directory_push_button.clicked.connect(self.output_directory_push_button_on_clicked)
        output_directory_h_layout.addWidget(self.output_directory_push_button)

        self.layout.addWidget(output_directory_h_layout_widget)


        buttons_h_layout_widget = QWidget()
        buttons_h_layout = QHBoxLayout(buttons_h_layout_widget)
        buttons_h_layout.setSpacing(5)
        buttons_h_layout.setContentsMargins(1, 5, 1, 5)

        self.update_push_button = QPushButton("Reload")
        self.update_push_button.setFixedWidth(100)
        self.update_push_button.clicked.connect(self.update_push_button_on_clicked)
        buttons_h_layout.addWidget(self.update_push_button)

        self.render_all_push_button = QPushButton("Render All")
        self.render_all_push_button.clicked.connect(self.render_all_push_button_on_clicked)
        buttons_h_layout.addWidget(self.render_all_push_button)

        self.all_modules_push_button = QPushButton("Modules")
        self.all_modules_push_button.setFixedWidth(100)
        self.all_modules_push_button.clicked.connect(self.all_modules_push_button_on_clicked)
        buttons_h_layout.addWidget(self.all_modules_push_button)

        self.layout.addWidget(buttons_h_layout_widget)

        self.scroll_area = CustomScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_list_widget = QWidget()
        self.scroll_list_layout = QVBoxLayout(self.scroll_list_widget)
        self.scroll_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_list_widget)

        self.layout.addWidget(self.scroll_area)

        self.scroll_area_label_list = []
        self.scroll_area_menu_button_list = []
        self.scroll_area_render_button_list = []
        self.scroll_area_script_table_list = []
        self.opened_script_index = 0

        self.screen_geometry = QGuiApplication.primaryScreen().geometry()

        self.directory_path = ""
        self.output_directory_path = ""

        set_dark_theme(self)

        default_project_dir = cacher["MainWindow:default_project_dir"]
        if default_project_dir:
            self.set_directory(default_project_dir)
        
    # --- EVENT HANDLERS --------------------------------------------------------------------------------

    def test_push_button_on_clicked(self):

        size = self.size()
        width = size.width()
        height = size.height()
        print(f"Current window size: {width}x{height}")

    def directory_push_button_on_clicked(self):
        new_path = QFileDialog.getExistingDirectory (self, application_name + " - Choose project directory", directory=os.path.dirname(self.directory_path))
        if os.path.isdir(new_path) and not os.path.abspath(new_path) == self.directory_path:
            self.set_directory(new_path)

    def directory_line_edit_on_return_pressed(self):
        new_path = self.directory_line_edit.text()
        if os.path.isdir(new_path) and not os.path.abspath(new_path) == self.directory_path:
            self.set_directory(new_path)
        self.directory_line_edit.clearFocus()

    def output_directory_push_button_on_clicked(self):
        new_path = QFileDialog.getExistingDirectory (self, application_name + " - Choose output directory", directory=os.path.dirname(self.output_directory_path))
        if os.path.isdir(new_path) and not os.path.abspath(new_path) == self.output_directory_path:
            self.set_output_directory(new_path)

    def output_directory_line_edit_on_return_pressed(self):
        new_path = self.output_directory_line_edit.text()
        if not os.path.abspath(new_path) == self.output_directory_path:
            self.set_output_directory(new_path)
        self.output_directory_line_edit.clearFocus()

    def render_all_push_button_on_clicked(self):
        self.tpl_project.render()
        window = ProgressBarWindow(self,self.tpl_project)
        window.show()
        self.color_tpl_names_on_scroll_list_labels()

    def all_modules_push_button_on_clicked(self):
        module_list_window = ModuleListWindow(self,self.tpl_project)
        module_list_window.show()

    def clickable_label_on_clicked(self, index):
        if self.tpl_project.load_failed(index):
            window = TplLogMessageBox(self,index)
            window.show()
            return

        if self.opened_script_index == index:
            if self.scroll_area_script_table_list[index].isHidden():
                table_view = self.scroll_area_script_table_list[index]
                table_model = table_view.model()
                table_view.setHidden(False)
                self.adjust_size()
            else:
                table_view = self.scroll_area_script_table_list[index]
                table_view.setHidden(True)
        else:
            table_view = self.scroll_area_script_table_list[self.opened_script_index]
            table_view.setHidden(True)

            table_view = self.scroll_area_script_table_list[index]
            table_model = table_view.model()
                
            table_view.setHidden(False)
            self.opened_script_index = index
            self.adjust_size()

    def update_push_button_on_clicked(self,path):
        self.tpl_project.update()
        self.resize_scroll_area_to_fit_tpl_list()
        self.list_tpl_names_on_scroll_list_labels()

    def render_button_on_clicked(self, index):
        self.tpl_project.render(index)
        window = ProgressBarWindow(self,self.tpl_project)
        window.show()
        self.color_tpl_names_on_scroll_list_labels()

    def log_menu_entry_on_clicked(self, index):
        window = TplLogMessageBox(self,index)
        window.show()

    def module_menu_entry_on_clicked(self, index):
        module_list_window = ModuleListWindow(self,self.tpl_project,index)
        module_list_window.show()
    
    # --- GUI METHODS -----------------------------------------------------------------------------------

    def set_directory(self,directory_path):

        directory_path = os.path.abspath(directory_path)
        cacher["MainWindow:default_project_dir"] = directory_path

        self.directory_path = directory_path
        self.directory_path_hash = hashlib.sha256(directory_path.encode()).hexdigest()[:16]
        self.directory_line_edit.setText(directory_path)

        p = TplProject(directory_path)
        self.tpl_project = p

        self.resize_scroll_area_to_fit_tpl_list()
        self.list_tpl_names_on_scroll_list_labels()

        output_directory_path = cacher["MainWindow:default_output_dir_for:"+self.directory_path_hash]
        if not output_directory_path:
            output_directory_path = os.path.abspath(os.path.join(directory_path,"Scripts"))
            output_directory_path.replace('/','\\')
            if not output_directory_path.endswith('\\'):
                output_directory_path+='\\'
        
        self.output_directory_path = output_directory_path
        self.output_directory_line_edit.setText(output_directory_path)
        self.tpl_project.set_output_directory(output_directory_path)

    def set_output_directory(self,output_directory_path):
        if not output_directory_path:
            output_directory_path = os.path.abspath(os.path.join(self.directory_path,"Scripts"))
        else:
            output_directory_path = os.path.abspath(output_directory_path)
        output_directory_path.replace('/','\\')
        if not output_directory_path.endswith('\\'):
            output_directory_path+='\\'
        cacher["MainWindow:default_output_dir_for:"+self.directory_path_hash] = output_directory_path
        self.output_directory_path = output_directory_path
        self.output_directory_line_edit.setText(output_directory_path)
        self.tpl_project.set_output_directory(output_directory_path)

    def resize_scroll_area_to_fit_tpl_list(self):
        # Clear the existing layout items
        while self.scroll_list_layout.count():
            item = self.scroll_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    # Recursively clear the nested layout
                    while layout.count():
                        nested_item = layout.takeAt(0)
                        nested_widget = nested_item.widget()
                        if nested_widget:
                            nested_widget.deleteLater()
                        else:
                            nested_layout = nested_item.layout()
                            if nested_layout:
                                while nested_layout.count():
                                    nested_nested_item = nested_layout.takeAt(0)
                                    nested_nested_widget = nested_nested_item.widget()
                                    if nested_nested_widget:
                                        nested_nested_widget.deleteLater()
                                    else:
                                        # Nested layouts within layouts (if any)
                                        nested_nested_layout = nested_nested_item.layout()
                                        if nested_nested_layout:
                                            while nested_nested_layout.count():
                                                double_nested_item = nested_nested_layout.takeAt(0)
                                                double_nested_widget = double_nested_item.widget()
                                                if double_nested_widget:
                                                    double_nested_widget.deleteLater()

        # Rebuild the layout based on the current self.tpl_project size
        self.scroll_area_label_list.clear()
        self.scroll_area_render_button_list.clear()
        self.scroll_area_script_table_list.clear()

        dlen = len(self.tpl_project)

        for i in range(dlen):
            entry_vbox_layout = QVBoxLayout()

            # ---------------------------------------------------------------------------

            entry_hbox_layout = QHBoxLayout()



            dropdown_button = QToolButton()
            dropdown_button.setIcon(QIcon(resource_path("assets\\icons\\dropdown-arrow-icon.png")))
            dropdown_button.setStyleSheet("""
                QToolButton {
                    border: none;
                    background: none;
                    padding: 0;
                    margin: 0;
                }
                QToolButton::menu-indicator {
                    image: none;
                }
            """)
            dropdown_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            dropdown_menu = QMenu()
            set_dark_theme(dropdown_menu)

            module_action = dropdown_menu.addAction("Modules")
            module_action.triggered.connect(lambda _, index=i: self.module_menu_entry_on_clicked(index))

            log_action = dropdown_menu.addAction("Log")
            log_action.triggered.connect(lambda _, index=i: self.log_menu_entry_on_clicked(index))

            dropdown_button.setMenu(dropdown_menu)

            entry_hbox_layout.addWidget(dropdown_button)



            label = ClickableLabel()
            label.clicked.connect(lambda index=i: self.clickable_label_on_clicked(index))
            self.scroll_area_label_list.append(label)
            entry_hbox_layout.addWidget(label)



            render_button = QPushButton("Render")
            render_button.setFixedWidth(100)
            render_button.clicked.connect(lambda _, index=i: self.render_button_on_clicked(index))
            self.scroll_area_render_button_list.append(render_button)
            entry_hbox_layout.addWidget(render_button)

            entry_vbox_layout.addLayout(entry_hbox_layout)

            # ---------------------------------------------------------------------------

            table_view = TplTableView(self)
            table_model = TplModel(table_view, self.tpl_project, i)
            table_view.setModel(table_model)
            table_view.setHidden(True)
            table_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            self.scroll_area_script_table_list.append(table_view)

            entry_vbox_layout.addWidget(table_view)

            # ---------------------------------------------------------------------------

            self.scroll_list_layout.addLayout(entry_vbox_layout)


    def list_tpl_names_on_scroll_list_labels(self):
        dlen = len(self.tpl_project)

        max_lable_width = 0
        for i in range(dlen):
            self.scroll_area_label_list[i].setText(self.tpl_project.name(i))

            if self.tpl_project.load_failed(i):
                table_view = self.scroll_area_script_table_list[i]
                if table_view.model():
                    table_view.model().deleteLater()
                table_view.setHidden(True)
                self.scroll_area_render_button_list[i].setEnabled(False)
            else:
                self.scroll_area_render_button_list[i].setEnabled(True)

            max_lable_width = max(max_lable_width, self.scroll_area_label_list[i].sizeHint().width())
        self.color_tpl_names_on_scroll_list_labels()
        self.adjust_size()

    def color_tpl_names_on_scroll_list_labels(self):
        dlen = len(self.tpl_project)
        for i in range(dlen):
            if self.tpl_project.load_failed(i):
                self.scroll_area_label_list[i].setStyleSheet('color: #FF3333;')
            elif self.tpl_project.render_failed(i):
                self.scroll_area_label_list[i].setStyleSheet('color: #FF9333;')
            else:
                self.scroll_area_label_list[i].setStyleSheet('color: #FFFFFF;')

    def adjust_size(self):
        
        if self.isMaximized():
            return

        dlen = len(self.tpl_project)

        if dlen==0:
            return

        max_lable_width = 0
        for i in range(dlen):
            max_lable_width = max(max_lable_width, self.scroll_area_label_list[i].sizeHint().width())

        total_height = 30 * dlen + 145 + (self.scroll_area_script_table_list[self.opened_script_index].height()+5 if not self.scroll_area_script_table_list[self.opened_script_index].isHidden() else 0)
        total_width = max(max_lable_width + 210,self.scroll_area_script_table_list[self.opened_script_index].sizeHint().width()+7 if not self.scroll_area_script_table_list[self.opened_script_index].isHidden() else 0)

        total_height = max(total_height,self.height())
        total_width = max(total_width,self.width())

        total_height = min(total_height,self.screen_geometry.height()-100)
        total_width = min(total_width,self.screen_geometry.width())

        self.resize(total_width, total_height)