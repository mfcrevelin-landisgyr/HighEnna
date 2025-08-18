from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *
from custom_classes import *

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
        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))
        self.adjust_size()
        self.init_ui()

        self.project = Project(self)

        self.application_cache = Cacher(os.path.join(user_cache_dir(APPLICATION_NAME),"application_cache.json"))

        current_project_path = self.application_cache['main_window:current_project_path']
        # print(current_project_path)
        if current_project_path and os.path.isdir(current_project_path):
            self.project.open(current_project_path)

        self.adjust_size()

    def init_ui(self):
        self.init_menubar()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QHBoxLayout(self.main_widget)

        self.tab_widget = CustomTabWidget()
        self.main_layout.addWidget(self.tab_widget, 1)

        # side_panel = QVBoxLayout()
        # main_layout.addLayout(side_panel)

        # self.new_tab_btn = QPushButton("New Tab")
        # self.new_tab_btn.clicked.connect(self.add_dummy_tab)
        # side_panel.addWidget(self.new_tab_btn)
        # side_panel.addStretch()

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
                {"option": "Exit", "keybinding": "Ctrl+Q", "slot": self.exit_slot}
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

#--- Menu Bar Slots --- #

    def open_project_slot(self):
        current_project_path = self.application_cache['main_window:current_project_path']
        last_project_paths = self.application_cache['main_window:last_project_paths']
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")

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
            self.project.open(new_path)

    def new_file_slot(self):
        QMessageBox.information(self, "new_file_slot", "new_file_slot")

    def save_all_slot(self):
        QMessageBox.information(self, "save_all_slot", "save_all_slot")

    def save_slot(self):
        QMessageBox.information(self, "save_slot", "save_slot")

    def render_all_slot(self):
        current_index = self.tab_widget.currentIndex()
        full_title = self.tab_widget.full_titles[current_index]
        QMessageBox.information(self, "render_all_slot", full_title)

    def render_slot(self):
        current_index = self.tab_widget.currentIndex()
        full_title = self.tab_widget.full_titles[current_index]
        QMessageBox.information(self, "render_slot", full_title)

    def exit_slot(self):
        if self.application_cache['main_window:current_project_path']:
            self.application_cache['main_window:current_project_path'] = ''
            self.project.close()
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

    def adjust_size(self, ratio=(3, 5)):
        numer, denom = 5,7

        screen = QApplication.screenAt(self.geometry().center())
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