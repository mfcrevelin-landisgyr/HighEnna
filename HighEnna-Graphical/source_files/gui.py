from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog, QMessageBox,
    QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QFileSystemWatcher, QEvent, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QCursor, QKeyEvent, QAction

from custom_qt import CScrollArea, CFooter, FileNameDialog
from project import *

from imports_window import ImportsWindow
from render_window import RenderWindow
from extensions_window import ExtensionsWindow
from docs_window import DocsWindow
from scenario_view import ScenarioView
from cacher import Cacher

from appdirs import user_cache_dir
from collections import defaultdict
import random
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

chars = [chr(ord('A')+i) for i in range(26)]+[chr(ord('0')+i) for i in range(10)]
def UUID():
    part1 = ''.join(random.choice(chars) for _ in range(4))
    part2 = ''.join(random.choice(chars) for _ in range(4))
    part3 = ''.join(random.choice(chars) for _ in range(4))
    part4 = ''.join(random.choice(chars) for _ in range(4))
    return f"{part1}-{part2}-{part3}-{part4}"

APPLICATION_NAME = "High Enna"

class UpdateWorker(QThread):
    scenario_changed = pyqtSignal()
    module_changed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        scenario_changed_b, module_change_b = self.parent.project.update()
        if scenario_changed_b:
            self.scenario_changed.emit()
        if module_change_b:
            self.module_changed.emit()

class MainWindow(QMainWindow):
    def __init__(self,init_path=None):
        super().__init__()

        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(resource_path("assets\\icons\\icon.png")))

        self.dictionary = {"main_window":self,"project":Project()}
        self.__dict__.update(self.dictionary)

        self.base_cache_path = os.path.join(user_cache_dir(APPLICATION_NAME),"application_cache_2_0_0.json")
        self.session_id = UUID()
        self.application_cache_path = self.base_cache_path.replace('.json',f'_{self.session_id}.json')
        while os.path.isfile(self.application_cache_path):
            self.session_id = UUID()
            self.application_cache_path = self.base_cache_path.replace('.json',f'_{self.session_id}.json')

        base_cache = Cacher(self.base_cache_path)
        self.application_cache = Cacher(self.application_cache_path)
        self.application_cache.update(base_cache)
        self.project.application_cache = self.application_cache

        self.application_cache.setdefault('current_project_path',None)
        self.application_cache.setdefault('last_project_paths',[])
        self.application_cache.setdefault('extensions',{
                # Python
                '.tpy': '.py',
                '.tpyw': '.pyw',

                # C-family
                '.tc': '.c',
                '.tcpp': '.cpp',
                '.tcc': '.cc',
                '.tcxx': '.cxx',
                '.th': '.h',
                '.thpp': '.hpp',
                '.thxx': '.hxx',

                # JavaScript / TypeScript
                '.tjs': '.js',
                '.tts': '.ts',
                '.tjsx': '.jsx',
                '.ttsx': '.tsx',

                # Shell / scripting
                '.tsh': '.sh',
                '.tbash': '.bash',
                '.tbat': '.bat',
                '.tps1': '.ps1',

                # Ruby / PHP / Perl
                '.trb': '.rb',
                '.tphp': '.php',
                '.tperl': '.pl',
                '.tpm': '.pm',

                # Go / R / Julia / Lua
                '.tgo': '.go',
                '.tr': '.r',
                '.tjulia': '.jl',
                '.tlua': '.lua',

                # Kotlin / Swift / Dart
                '.tkt': '.kt',
                '.tkts': '.kts',
                '.tswift': '.swift',
                '.tdart': '.dart',

                # SQL
                '.tsql': '.sql',

                # Java & Groovy
                '.tjava': '.java',
                '.tgroovy': '.groovy',
            })

        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_watcher_directory_changed)
        self.watch_debouncer = QTimer()
        self.watch_debouncer.setSingleShot(True)
        self.watch_debouncer.timeout.connect(self.on_watch_debouncer_timeout)
        
        global desktop_path
        desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")

        self.scenario_views = {}
        self.active_scenario_view=None

        self.extensions_window = None
        self.imports_window = None
        self.render_window = None
        self.docs_window = None

        self.init_ui()

        current_project_path = init_path
        project_opened = False
        if current_project_path and os.path.isdir(current_project_path):
            project_opened = self.open_project(current_project_path, open_ok=True)
        if not project_opened:
            current_project_path = self.application_cache['current_project_path']
            if current_project_path and os.path.isdir(current_project_path):
                project_opened = self.open_project(current_project_path, open_ok=True)
        if not project_opened:
            self.application_cache['current_project_path'] = None

        self.adjust_size()


    def init_ui(self):
        self.init_menubar()

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout(self.main_widget)

        self.scroll_area = CScrollArea(self.main_widget)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QWidget(self.scroll_area)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.main_layout.addWidget(self.scroll_area)

        self.footer = CFooter()

        self.main_layout.addWidget(self.footer)

    def init_menubar(self):

        menu_bar = self.menuBar()

        # Define menu structure
        self.menus = {
            "File": [
                {"option": "Open Project Folder   ", "keybinding": "Ctrl+Shift+O", "slot": self.open_project_folder_slot},
                {"option": "Open Project", "keybinding": "Ctrl+O", "slot": self.open_project_slot},
                {"option": "New Module", "keybinding": "Ctrl+M", "slot": self.new_module_slot},
                {"option": "New File", "keybinding": "Ctrl+N", "slot": self.new_file_slot},
                None,
                {"option": "Save All", "keybinding": "Ctrl+Shift+S", "slot": self.save_all_slot},
                {"option": "Save", "keybinding": "Ctrl+S", "slot": self.save_slot},
                None,
                {"option": "Render All", "keybinding": "Ctrl+Shift+R", "slot": self.render_all_slot},
                {"option": "Render", "keybinding": "Ctrl+R", "slot": self.render_slot},
                None,
                {"option": "Close Project", "keybinding": "Ctrl+W", "slot": self.close_project_slot},
                {"option": "Exit", "keybinding": "Ctrl+Q", "slot": self.close},
            ],
            "Edit": [
                {"option": "Imports", "keybinding": "Ctrl+I", "slot": self.imports_slot},
                {"option": "Extentions", "keybinding": "Ctrl+Shift+E", "slot": self.extensions_slot},
                None,
                {"option": "Render path", "keybinding": "Ctrl+E", "slot": self.render_path_slot},
            ],
            "View": [
                {"option": "Colapse All", "keybinding": "Ctrl+Left", "slot": self.colapse_all_slot},
                {"option": "Expand All", "keybinding": "Ctrl+Right", "slot": self.expand_all_slot},
            ],
            "Help": [
                {"option": "Documentation", "keybinding": "Ctrl+D", "slot": self.documentation_slot},
                {"option": "About", "keybinding": "Ctrl+1", "slot": self.about_slot},
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
        if self.project.is_open:
            def on_scenario_changed():
                if self.render_window:
                    self.render_window.close()
                    self.render_window = None
                self.populate()

            def on_module_changed():
                if self.imports_window:
                    self.imports_window.update()


            worker = UpdateWorker(self)

            worker.scenario_changed.connect(on_scenario_changed)
            worker.module_changed.connect(on_module_changed)

            worker.finished.connect(worker.deleteLater)

            worker.start()

#--- Menu Bar Slots --- #

    def open_project_folder_slot(self):
        os.system(f'explorer "{self.application_cache["current_project_path"]}"')

    def open_project_slot(self):
        current_project_path = self.application_cache['current_project_path']
        last_project_paths = self.application_cache['last_project_paths']

        last_project_paths = [p for p in last_project_paths if os.path.isdir(p)]
        last_project_paths = list(dict.fromkeys(last_project_paths))[:10]

        self.application_cache['last_project_paths'] = last_project_paths

        paths = [current_project_path] + last_project_paths
        start_dir = next((os.path.dirname(path) for path in paths if path and os.path.isdir(path)),desktop_path)

        new_path = QFileDialog.getExistingDirectory(self,APPLICATION_NAME + " - Choose Project",directory=start_dir)

        if new_path and os.path.isdir(new_path) and not os.path.abspath(new_path) == current_project_path:
            self.open_project(new_path)

    def new_file_slot(self,init_text=''):
        current_project_path = self.project.project_path
        if not current_project_path:
            CFooter.broadcast("There is no project open.", 1500)
            return

        def after_accept(name):
            if not name:
                return

            if '.' not in name:
                QMessageBox.warning(self, "Invalid Filename", "Filename must include an extension.")
                self.new_file_slot(name)
                return

            ext = name.rsplit('.', 1)[-1]

            if f'.{ext}' not in self.application_cache['extensions']:
                QMessageBox.warning(self, "Invalid Extension",
                    f"Extension '.{ext}' is not a valid scenario extension.\nUse Ctrl+Shift+E to manage valid extensions.")
                self.new_file_slot(name)
                return

            file_path = os.path.join(current_project_path, name)

            if os.path.exists(file_path):
                QMessageBox.warning(self, "File Exists", f"The file '{name}' already exists.")
                self.new_file_slot(name)
                return

            try:
                with open(file_path, 'bw') as f:
                    f.write(b'')
                os.system(f'start "" "{file_path}"')
            except Exception as e:
                QMessageBox.critical(self, "File Creation Failed", f"Failed to create file: {str(e)}")

        win = FileNameDialog(self,init_text)
        win.nameAccepted.connect(after_accept)
        win.finished.connect(win.deleteLater)
        win.show()

    def new_module_slot(self):
        current_modules_path = self.project.modules_path
        if not current_modules_path:
            CFooter.broadcast("There is no project open.", 1500)
            return

        def after_accept(name: str):

            if not name:
                return

            if not name.endswith(".py"):
                name += ".py"

            file_path = os.path.join(current_modules_path, name)

            if os.path.exists(file_path):
                QMessageBox.warning(self, "File Exists", f"The file '{name}' already exists.")
                return

            try:
                with open(file_path, 'bw') as f:
                    f.write(b'')
                os.system(f'start "" "{file_path}"')
            except Exception as e:
                QMessageBox.critical(self, "File Creation Failed", f"Failed to create file: {str(e)}")

        win = FileNameDialog(self)
        win.nameAccepted.connect(after_accept)
        win.finished.connect(win.deleteLater)
        win.show()

    def save_all_slot(self):
        any_cache_error = False
        for scenario_file in self.project.scenario_files.values():
            any_cache_error |= scenario_file.cache_error
            if not scenario_file.cache_error:
                scenario_file.save()
        if any_cache_error:
            CFooter.broadcast("Some scripts did not save. Look for Cache errors...", 2500)
        else:
            CFooter.broadcast("All scripts saved.", 1500)

    def save_slot(self):
        active_scenario_entry = self.project.project_cache['active_scenario_entry']
        if active_scenario_entry:
            if self.project.scenario_files[active_scenario_entry].cache_error:
                CFooter.broadcast("{script} did not save. Look for Cache errors...".format(script=active_scenario_entry), 2500)
            else:
                self.project.scenario_files[active_scenario_entry].save()
                CFooter.broadcast("{script} saved.".format(script=active_scenario_entry), 1500)
        else:
            CFooter.broadcast("No script selected.", 1500)

    def render_all_slot(self):
        if not self.render_window:
            items = {
                scenario_file_name: (list(range(len(scenario_file.scripts_table))) if scenario_file.scripts_table else [-1])
                for scenario_file_name, scenario_file in self.project.scenario_files.items()
                if scenario_file.scripts_table or scenario_file.vals_table
            }
            if not items:
                CFooter.broadcast("No scripts to render.", 2500)
                return
            def render_window_on_finished():
                self.render_window.deleteLater()
                self.render_window = None
            self.render_window = RenderWindow(self,items)
            self.render_window.finished.connect(render_window_on_finished)
            self.render_window.show()
        else:
            CFooter.broadcast("Rendering window is open.", 2500)

    def render_slot(self):
        active_scenario_entry = self.project.project_cache['active_scenario_entry']
        if active_scenario_entry:
            if not self.render_window:
                scenario_file = self.project.scenario_files[active_scenario_entry]

                if scenario_file.scripts_table:  # Non-empty scripts_table
                    items = {active_scenario_entry: list(range(len(scenario_file.scripts_table)))}
                elif scenario_file.vals_table:  # Empty scripts_table but non-empty vals_table
                    items = {active_scenario_entry: [-1]}
                else:
                    CFooter.broadcast("No scripts to render.", 2500)
                    return

                def render_window_on_finished():
                    self.render_window.deleteLater()
                    self.render_window = None

                items = {active_scenario_entry:list(range(len(scenario_file.scripts_table)))}
                self.render_window = RenderWindow(self,items)
                self.render_window.finished.connect(render_window_on_finished)
                self.render_window.show()
            else:
                CFooter.broadcast("Rendering already in progress.", 2500)
        else:
            CFooter.broadcast("No script selected.", 1500)

    def close_project_slot(self):
        self.application_cache['current_project_path'] = None
        self.close_project()

    def extensions_slot(self):
        def extensions_window_on_finished():
            self.extensions_window.deleteLater()
            self.extensions_window = None

        def extensions_window_on_config_accepted(result):
            self.application_cache['extensions'] = result

            worker = UpdateWorker(self)

            worker.scenario_changed.connect(self.populate)
            worker.module_changed.connect(lambda: self.imports_window.update() if self.imports_window else None)

            worker.finished.connect(worker.deleteLater)

            worker.start()

        self.extensions_window = ExtensionsWindow(self,self.application_cache['extensions'])
        self.extensions_window.finished.connect(extensions_window_on_finished)
        self.extensions_window.configAccepted.connect(extensions_window_on_config_accepted)
        self.extensions_window.show()

    def render_path_slot(self):
        if self.project.is_open:
            start_dir = self.project.project_cache['render_dir']
            if not os.path.isdir(start_dir):
                start_dir = self.project.project_path
            output_dir_path = QFileDialog.getExistingDirectory(self,APPLICATION_NAME + " - Choose Output Directory",directory=start_dir)

            if output_dir_path and os.path.isdir(output_dir_path):
                if os.path.normcase(os.path.abspath(output_dir_path)) == os.path.normcase(os.path.abspath(self.project.project_path)):
                    output_dir_path = os.path.join(self.project.project_path,'scripts')
                self.project.project_cache['render_dir'] = output_dir_path
        else:
            CFooter.broadcast("No project open.", 1500)

    def imports_slot(self):
        if self.project.is_open:

            def imports_window_on_finished():
                self.imports_window.deleteLater()
                self.imports_window = None

            def imports_window_on_applied(result):
                self.project.project_cache["modules"]['module_assignments'] = result

                for scenario_file in self.project.scenario_files.values():
                    scenario_file.update_modules()

            self.imports_window = ImportsWindow(self)
            self.imports_window.finished.connect(imports_window_on_finished)
            self.imports_window.applied.connect(imports_window_on_applied)
            self.imports_window.show()

        else:
            CFooter.broadcast("No project open.", 1500)

    def documentation_slot(self):
        if not self.docs_window:
            self.docs_window = DocsWindow()
            self.docs_window.closed.connect(lambda: setattr(self, "docs_window", None))
            self.docs_window.show()
        else:
            CFooter.broadcast("Documentation already open.", 1500)

    def about_slot(self):
        CFooter.broadcast("about_slot", 1500)

    def colapse_all_slot(self):
        self.project.project_cache['active_scenario_entry'] = None
        for scenario_view in self.scenario_views.values():
            if not scenario_view.project_cache["is_closed"]:
                scenario_view.on_title_label_left_clicked(True)
            if not scenario_view.project_cache["is_closed"]:
                scenario_view.on_title_label_left_clicked(True)

    def expand_all_slot(self):
        self.project.project_cache['active_scenario_entry'] = None
        for scenario_view in self.scenario_views.values():
            if scenario_view.project_cache["is_closed"]:
                scenario_view.on_title_label_left_clicked(True)

#--- Main Window Utils --- #

    def check_obsolete(self):

        obsolete_by_file = defaultdict(dict)
        for scenario_file_key, scenario_file in self.project.scenario_files.items():
            obsolete_vars = [var for var in scenario_file.vars_table.column_names
                             if var not in scenario_file.result_parse['names']['vars']]
            obsolete_vals = [val for val in scenario_file.vals_table.column_names
                             if val not in scenario_file.result_parse['names']['vals']]

            if obsolete_vars:
                obsolete_by_file[scenario_file_key]['vars'] = obsolete_vars
            if obsolete_vals:
                obsolete_by_file[scenario_file_key]['vals'] = obsolete_vals

            if obsolete_vars or obsolete_vals:
                scenario_file.remove_obsolete()

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
                "\n\nThis is not permanent until you save the file(s)."
            )

            msg.setText(text)
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)

            QTimer.singleShot(50,msg.exec)

    def populate(self):
        self.clear()
        self.check_obsolete()
        for scenario_file_key, scenario_file in sorted(self.project.scenario_files.items(), key=lambda x: x[0]):
            self.scenario_views[scenario_file_key] = ScenarioView(scenario_file,self.dictionary)
        for entry in [entry for entry in self.project.project_cache['scenarioview'] if entry not in self.project.scenario_files.keys()]:
            self.project.project_cache['scenarioview'].pop(entry)

    def clear(self):
        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    _clear_layout(item.layout())
        _clear_layout(self.scroll_area_layout)
        self.scenario_views.clear()

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

    def open_project(self,new_path,open_ok=False):
        op_result = self.project.open(new_path)

        if op_result:
            self.application_cache['current_project_path'] = os.path.abspath(new_path)
            self.application_cache['last_project_paths'].insert(0, os.path.abspath(new_path))
            self.main_window.menu_widgets['File']['Close Project'].setEnabled(True)
            self.setWindowTitle(APPLICATION_NAME + ' - (' + self.project.project_name + ')')
            self.project.project_cache['active_scenario_entry'] = None
            self.watcher.addPaths([new_path,self.project.modules_path])
            self.populate()
        elif not open_ok:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Project already open")

            msg.setText("The project is already open in another window.\n\n")
            msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)

            QTimer.singleShot(50,msg.exec)

        return op_result

    def close_project(self):
        self.main_window.menu_widgets['File']['Close Project'].setEnabled(False)
        remove_paths = self.watcher.files()+self.watcher.directories()
        if remove_paths:
            self.watcher.removePaths(remove_paths)
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
        if self.imports_window:
            self.imports_window.close()
        if self.docs_window:
            self.docs_window.close()
        if self.render_window:
            self.render_window.close()

        def finish():
            self.project.close()
            base_cache = Cacher(self.base_cache_path)
            base_cache.update(self.application_cache)
            os.remove(self.application_cache_path)

        if any(scenario_file.has_unsaved_changes() for scenario_file in self.project.scenario_files.values()):
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_slot()
                finish()
                super().closeEvent(event)
            elif reply == QMessageBox.StandardButton.Discard:
                finish()
                super().closeEvent(event)
            else:  # Cancel
                event.ignore()
        else:
            finish()
            super().closeEvent(event)
