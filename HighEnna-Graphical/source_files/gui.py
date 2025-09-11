from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from project import *
from custom_qt import *

from cacher import Cacher
from tpy_view import TpyView

from appdirs import user_cache_dir
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dictionary = {"main_window":self}
        self.__dict__.update(self.dictionary)
        
        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))
        self.init_ui()

        self.project = Project()
        self.entries = []
        self.open_entries = []

        self.application_cache = Cacher(os.path.join(user_cache_dir(APPLICATION_NAME),"application_cache.json"))
        
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_watcher_directory_changed)
        self.watch_debouncer = QTimer()
        self.watch_debouncer.setSingleShot(True)
        self.watch_debouncer.timeout.connect(self.on_watch_debouncer_timeout)

        current_project_path = self.application_cache['main_window:current_project_path']
        if current_project_path and os.path.isdir(current_project_path):
            self.open_project(current_project_path)

        self.adjust_size()

        global desktop_path
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")


    def init_ui(self):
        self.init_menubar()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout(self.main_widget)

        self.scroll_area = CScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.main_layout.addWidget(self.scroll_area)
        

    def init_menubar(self):

        menu_bar = self.menuBar()

        # Define menu structure
        self.menus = {
            "File": [
                {"option": "Open Project", "keybinding": "Ctrl+O", "slot": self.open_project_slot},
                {"option": "New File", "keybinding": "Ctrl+N", "slot": self.new_file_slot},
                None,
                {"option": "Save All", "keybinding": "Ctrl+Shift+S", "slot": self.save_all_slot},
                {"option": "Save", "keybinding": "Ctrl+S", "slot": self.save_slot},
                None,
                {"option": "Render All", "keybinding": "Ctrl+Shift+R", "slot": self.render_all_slot},
                {"option": "Render", "keybinding": "Ctrl+R", "slot": self.render_slot},
                None,
                {"option": "Open Containing Folder   ", "keybinding": "", "slot": self.open_containing_folder_slot},
                {"option": "Exit", "keybinding": "Ctrl+W", "slot": self.exit_slot}
            ],
            "Edit": [
                None,
                {"option": "Undo", "keybinding": "Ctrl+Z", "slot": self.undo_slot},
                {"option": "Redo", "keybinding": "Ctrl+Y", "slot": self.redo_slot},
                None,
                {"option": "Prefereces", "keybinding": None, "slot": self.prefereces_slot}
            ],
            "View": [
                {"option": "Imports", "keybinding": "Ctrl+M", "slot": self.imports_slot}
            ],
            "Help": [
                {"option": "Documentation", "keybinding": None, "slot": self.documentation_slot},
                {"option": "About", "keybinding": None, "slot": self.about_slot}
            ]
        }

        for menu_name, options in self.menus.items():
            menu = QMenu(menu_name, self)
            for entry in options:

                if entry is None:
                    menu.addSeparator()
                    continue

                action = QAction(entry["option"], self)
                if entry["keybinding"]:
                    action.setShortcut(QKeySequence(entry["keybinding"]))
                if callable(entry["slot"]):
                    action.triggered.connect(entry["slot"])
                menu.addAction(action)
            menu_bar.addMenu(menu)

#--- Slots --- #
    
    def on_watcher_directory_changed(self):
        self.watch_debouncer.start(50)
    
    def on_watch_debouncer_timeout(self):
        self.project.update()
        self.populate()

#--- Menu Bar Slots --- #

    def open_containing_folder_slot(self):
        os.system(f'explorer "{self.application_cache["main_window:current_project_path"]}"')

    def open_project_slot(self):
        current_project_path = self.application_cache['main_window:current_project_path']
        last_project_paths = self.application_cache['main_window:last_project_paths']

        if last_project_paths is None:
            last_project_paths = self.application_cache['main_window:last_project_paths'] = []
        else:
            last_project_paths =  list(set(project_path for project_path in last_project_paths if os.path.isdir(project_path)))
            self.application_cache['main_window:last_project_paths'] = last_project_paths[:5]


        paths = [current_project_path] + last_project_paths
        start_dir = next((os.path.dirname(path) for path in paths if path and os.path.isdir(path)),desktop_path)

        new_path = QFileDialog.getExistingDirectory(self,APPLICATION_NAME + " - Choose Project",directory=start_dir)

        if new_path and os.path.isdir(new_path) and not os.path.abspath(new_path) == current_project_path:
            self.application_cache['main_window:current_project_path'] = os.path.abspath(new_path)
            self.application_cache['main_window:last_project_paths'].insert(0, os.path.abspath(new_path))
            self.open_project(new_path)

    def new_file_slot(self):
        current_project_path = self.application_cache['main_window:current_project_path']
        if not current_project_path:
            QMessageBox.warning(self, "No Project Open", "There is no project open.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Create New File",
                current_project_path,
                "TPY Files (*.tpy)",
                options=QFileDialog.Option.DontConfirmOverwrite
            )

        if not file_path:
            return

        if not file_path.endswith(".tpy"):
            file_path += ".tpy"

        if os.path.exists(file_path):
            QMessageBox.warning(self, "File Exists", f"The file '{os.path.basename(file_path)}' already exists.")
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create file:\n{e}")
            return



    def save_all_slot(self):
        QMessageBox.information(self, "save_all_slot", "save_all_slot")

    def save_slot(self):
        QMessageBox.information(self, "save_slot", "save_slot")

    def render_all_slot(self):
        QMessageBox.information(self, "render_all_slot", "render_all_slot")

    def render_slot(self):
        QMessageBox.information(self, "render_slot", "render_slot")

    def exit_slot(self):
        if self.application_cache['main_window:current_project_path']:
            self.application_cache['main_window:current_project_path'] = ''
            self.close_project()
        else:
            self.close()

    def undo_slot(self):
        QMessageBox.information(self, "undo_slot", "undo_slot")

    def redo_slot(self):
        QMessageBox.information(self, "redo_slot", "redo_slot")

    def prefereces_slot(self):
        QMessageBox.information(self, "prefereces_slot", "prefereces_slot")

    def imports_slot(self):
        QMessageBox.information(self, "imports_slot", "imports_slot")

    def documentation_slot(self):
        QMessageBox.information(self, "documentation_slot", "documentation_slot")

    def about_slot(self):
        QMessageBox.information(self, "about_slot", "about_slot")


#--- Main Window Utils --- #

    def populate(self):
        self.clear()
        for idx,tpy_file_key in enumerate(sorted(self.project.tpy_files)):
            self.entries.append(TpyView(idx,self.project.tpy_files[tpy_file_key],self.dictionary))

    def clear(self):
        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    _clear_layout(item.layout())
        _clear_layout(self.scroll_area_layout)
        self.entries.clear()

    def parse_keybinding(keybinding):
        parts = keybinding.split("+")
        mods = Qt.KeyboardModifier(0)
        key = None
        mod_map = {
            "Ctrl": Qt.KeyboardModifier.ControlModifier,
            "Shift": Qt.KeyboardModifier.ShiftModifier,
            "Alt": Qt.KeyboardModifier.AltModifier,
            "Meta": Qt.KeyboardModifier.MetaModifier,
        }
        for part in parts:
            if part in mod_map:
                mods |= mod_map[part]
            else:
                # For the key part, use Qt.Key enum names, e.g. "N" -> Qt.Key_N
                key_name = "Key_" + part.upper()
                key = getattr(Qt, key_name, None)
                if key is None:
                    raise ValueError(f"Unknown key: {part}")
        return mods, key

    def adjust_size(self):
        numer, denom = 5,7

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()

        available_geometry = screen.availableGeometry()

        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        new_width = screen_width * numer // denom
        new_height = screen_height * numer // denom

        new_x = available_geometry.x() + screen_width * (denom - numer) // (2 * denom)
        new_y = available_geometry.y() + screen_height * (denom - numer) // (2 * denom)

        self.setGeometry(new_x, new_y, new_width, new_height)


#--- Main Window Methods --- #

    def open_project(self,new_path):
        self.project.open(new_path)
        self.setWindowTitle(APPLICATION_NAME + ' - ' + self.project.project_name)
        self.populate()
        self.watcher.addPath(new_path)

    def close_project(self):
        self.watcher.removePaths(self.watcher.files())
        self.watcher.removePaths(self.watcher.directories())
        self.project.close()
        self.setWindowTitle(APPLICATION_NAME)
        self.clear()
        self.open_entries.clear()

    def keyPressEvent(self, event: QKeyEvent):
        pressed_mods = event.modifiers()
        pressed_key = event.key()

        for menu_items in self.menus.values():
            for item in menu_items:
                if not item or not item.get("keybinding"):
                    continue

                try:
                    mods, key = parse_keybinding(item["keybinding"])
                except Exception:
                    continue

                if mods == pressed_mods and key == pressed_key:
                    item["slot"]()
                    return

    def closeEvent(self, event):
        super().closeEvent(event)