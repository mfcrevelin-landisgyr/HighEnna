from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *
from project import *

from tpy_view import TpyView
from cacher import Cacher

from appdirs import user_cache_dir
from collections import defaultdict
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

        self.dictionary = {"main_window":self,"project":Project()}
        self.__dict__.update(self.dictionary)

        self.application_cache = Cacher(os.path.join(user_cache_dir(APPLICATION_NAME),"application_cache.json"))

        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_watcher_directory_changed)
        self.watch_debouncer = QTimer()
        self.watch_debouncer.setSingleShot(True)
        self.watch_debouncer.timeout.connect(self.on_watch_debouncer_timeout)

        global desktop_path
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")

        self.tpy_views = {}
        self.active_tpy_view=None
        
        self.init_ui()

        current_project_path = self.application_cache['main_window']['current_project_path']
        if current_project_path and os.path.isdir(current_project_path):
            self.open_project(current_project_path)

        self.adjust_size()


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
                {"option": "Open Containing Folder   ", "keybinding": "Ctrl+Shift+O", "slot": self.open_containing_folder_slot},
                {"option": "Open Project", "keybinding": "Ctrl+O", "slot": self.open_project_slot},
                {"option": "New File", "keybinding": "Ctrl+N", "slot": self.new_file_slot},
                None,
                {"option": "Save All", "keybinding": "Ctrl+Shift+S", "slot": self.save_all_slot},
                {"option": "Save", "keybinding": "Ctrl+S", "slot": self.save_slot},
                None,
                {"option": "Render All", "keybinding": "Ctrl+Shift+R", "slot": self.render_all_slot},
                {"option": "Render", "keybinding": "Ctrl+R", "slot": self.render_slot},
                None,
                {"option": "Exit", "keybinding": "Ctrl+W", "slot": self.exit_slot},
            ],
            "Edit": [
                {"option": "Imports", "keybinding": "Ctrl+M", "slot": self.imports_slot},
                None,
                {"option": "Prefereces", "keybinding": "Ctrl+P", "slot": self.prefereces_slot},
            ],
            "View": [
                {"option": "Colapse All", "keybinding": None, "slot": self.colapse_all_slot},
            ],
            "Help": [
                {"option": "Documentation", "keybinding": "Ctrl+1", "slot": self.documentation_slot},
                {"option": "About", "keybinding": "Ctrl+2", "slot": self.about_slot},
            ]
        }

        self.menu_widgets ={}

        for menu_name, options in self.menus.items():
            menu = QMenu(menu_name, self)
            self.menu_widgets[menu_name] = {"menu":menu}
            for entry in options:

                if entry is None:
                    menu.addSeparator()
                    continue

                action = QAction(entry["option"], self)
                self.menu_widgets[menu_name][entry["option"]] = action

                if entry["keybinding"]:
                    action.setShortcut(QKeySequence(entry["keybinding"]))
                if callable(entry["slot"]):
                    action.triggered.connect(entry["slot"])
                menu.addAction(action)
            menu_bar.addMenu(menu)

        self.main_window.menu_widgets['File']['Save'].setEnabled(False)
        self.main_window.menu_widgets['File']['Render'].setEnabled(False)

#--- Slots --- #
    
    def on_watcher_directory_changed(self):
        self.watch_debouncer.start(50)
    
    def on_watch_debouncer_timeout(self):
        if self.project.update():
            self.populate()

#--- Menu Bar Slots --- #

    def open_containing_folder_slot(self):
        os.system(f'explorer "{self.application_cache["main_window"]["current_project_path"]}"')

    def open_project_slot(self):
        current_project_path = self.application_cache['main_window']['current_project_path']
        last_project_paths = self.application_cache['main_window']['last_project_paths']

        if last_project_paths is None:
            last_project_paths = self.application_cache['main_window']['last_project_paths'] = []
        else:
            last_project_paths =  list(set(project_path for project_path in last_project_paths if os.path.isdir(project_path)))
            self.application_cache['main_window']['last_project_paths'] = last_project_paths[:5]


        paths = [current_project_path] + last_project_paths
        start_dir = next((os.path.dirname(path) for path in paths if path and os.path.isdir(path)),desktop_path)

        new_path = QFileDialog.getExistingDirectory(self,APPLICATION_NAME + " - Choose Project",directory=start_dir)

        if new_path and os.path.isdir(new_path) and not os.path.abspath(new_path) == current_project_path:
            self.application_cache['main_window']['current_project_path'] = os.path.abspath(new_path)
            self.application_cache['main_window']['last_project_paths'].insert(0, os.path.abspath(new_path))
            self.open_project(new_path)

    def new_file_slot(self):
        current_project_path = self.application_cache['main_window']['current_project_path']
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
        for tpy_file in self.project.tpy_files.values():
            tpy_file.save()
        msg = QMessageBox(self)
        msg.setWindowTitle("Save")
        msg.setText("Saved.")
        msg.exec()

    def save_slot(self):
        active_tpy_entry = self.project.project_cache['active_tpy_entry']
        if active_tpy_entry:
            self.project.tpy_files[active_tpy_entry].save()
        msg = QMessageBox(self)
        msg.setWindowTitle("Save")
        msg.setText("Saved.")
        msg.exec()

    def render_all_slot(self):
        QMessageBox.information(self, "render_all_slot", "render_all_slot")

    def render_slot(self):
        QMessageBox.information(self, "render_slot", "render_slot")

    def exit_slot(self):
        if self.application_cache['main_window']['current_project_path']:
            self.application_cache['main_window']['current_project_path'] = ''
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

    def colapse_all_slot(self):
        self.project.project_cache['active_tpy_entry']=None
        for tpy_view in self.tpy_views.values():
            tpy_view.tab_widget.setHidden(True)
            tpy_view.cache["is_closed"] = True

            font = tpy_view.title_label.font()
            font.setBold(False)
            tpy_view.title_label.setFont(font)

#--- Main Window Utils --- #

    def check_obsolete(self):

        obsolete_by_file = defaultdict(dict)
        for tpy_file_key, tpy_file in self.project.tpy_files.items():
            obsolete_vars = [var for var in tpy_file.vars_table.column_names
                             if var not in tpy_file.parse_result['names']['vars']]
            obsolete_vals = [val for val in tpy_file.vals_table.column_names
                             if val not in tpy_file.parse_result['names']['vals']]

            if obsolete_vars:
                obsolete_by_file[tpy_file_key]['vars'] = obsolete_vars
            if obsolete_vals:
                obsolete_by_file[tpy_file_key]['vals'] = obsolete_vals

            if obsolete_vars or obsolete_vals:
                tpy_file.remove_obsolete()

        if obsolete_by_file:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Obsolete Variables/Values Removed")

            text = "Some obsolete variables or values were automatically removed:\n\n"
            for key, names in obsolete_by_file.items():
                text += f"{key}:\n"
                if "vars" in names:
                    text += f"  vars: {', '.join(names['vars'])}\n"
                if "vals" in names:
                    text += f"  vals: {', '.join(names['vals'])}\n"

            text += (
                "\nIf needed, you can undo this action by going to the relevant\ntable(s) and pressing Ctrl+Z."
                "\n\nThis is not permanent until you save to file."
            )

            msg.setText(text)
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
            
            QTimer.singleShot(50,msg.exec)

    def populate(self):
        self.clear()
        self.check_obsolete()
        for tpy_file_key, tpy_file in sorted(self.project.tpy_files.items(), key=lambda x: x[0]):
            self.tpy_views[tpy_file_key] = TpyView(tpy_file,self.dictionary)
        for entry in [entry for entry in self.project.project_cache['tpyview'] if entry not in self.project.tpy_files.keys()]:
            self.project.project_cache['tpyview'].pop(entry)


    def clear(self):
        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    _clear_layout(item.layout())
        _clear_layout(self.scroll_area_layout)
        self.tpy_views.clear()

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
        self.setWindowTitle(APPLICATION_NAME + ' - (' + self.project.project_name + ')')
        self.project.project_cache['active_tpy_entry'] = None
        self.watcher.addPath(new_path)
        self.populate()

    def close_project(self):
        self.watcher.removePaths(self.watcher.files())
        self.watcher.removePaths(self.watcher.directories())
        self.project.close()
        self.setWindowTitle(APPLICATION_NAME)
        self.clear()

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