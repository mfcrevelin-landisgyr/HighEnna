from PyQt6.QtWidgets import (
    QFrame,QVBoxLayout,QHBoxLayout,QPushButton,
    QMenu,QWidget,QInputDialog
)
from PyQt6.QtGui import QFont

from custom_qt import (
        CFrame, CLabel, CTabWidget, 
        CTableView,  CErrorTableView
    )

from render_window import RenderWindow
from custom_qt import CFooter, FileNameDialog

import re
import os

class ScenarioView:
    def __init__(self,scenario_file,dictionary):
        self.dictionary = {'scenario_view':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.project_cache = self.project.project_cache['scenarioview'][scenario_file.scenario_name]
        self.project_cache.setdefault("is_closed",True)
        self.project_cache.setdefault("active_tab",None)

        self.scenario_file = scenario_file

        self.frame = CFrame(self.main_window.scroll_area_widget)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.clicked.connect(self.on_frame_clicked)
        self.vbox_layout = QVBoxLayout(self.frame)
        self.main_window.scroll_area_layout.addWidget(self.frame)
        self.populate()

    # ---- Slots ----

    def on_frame_clicked(self):
        active_key = self.project.project_cache['active_scenario_entry']
        is_active = active_key == self.scenario_file.scenario_name
        is_closed = self.project_cache['is_closed']

        if not is_active:
            def update_menu_bar(state):
                self.main_window.menu_widgets['File']['Save'].setEnabled(state)
                self.main_window.menu_widgets['File']['Render'].setEnabled(state)
                
            # Deactivate currently active scenario if any
            if active_key in self.main_window.scenario_views:
                active_view = self.main_window.scenario_views[active_key]
                font = active_view.title_label.font()
                font.setBold(False)
                active_view.title_label.setFont(font)

            # Activate this one
            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)

            self.project.project_cache['active_scenario_entry'] = self.scenario_file.scenario_name

            if is_closed and ((self.scenario_file.vars_table) or (self.scenario_file.vals_table) or (self.scenario_file.errors_table.data)):
                self.tab_widget.setHidden(False)
                self.project_cache["is_closed"] = False

            update_menu_bar(True)

    def on_title_label_left_clicked(self,ignore_footer=False):
        active_key = self.project.project_cache['active_scenario_entry']
        is_active = active_key == self.scenario_file.scenario_name
        is_closed = self.project_cache['is_closed']

        if is_active:

            if is_closed: # CASE 1: not open & active → open

                if (self.scenario_file.vars_table) or (self.scenario_file.vals_table) or (self.scenario_file.errors_table.data):
                    self.tab_widget.setHidden(False)
                    self.project_cache["is_closed"] = False
                elif not ignore_footer:
                    CFooter.broadcast("Nothing to edit on {script}.".format(script=self.scenario_file.scenario_name), 1500)

            elif not is_closed: # CASE 2: open & active → close

                self.tab_widget.setHidden(True)
                self.project_cache["is_closed"] = True

    def on_title_label_right_clicked(self):
        menu = QMenu(self.main_window)

        open_action = menu.addAction("Open" if self.project_cache["is_closed"] else "Close")
        menu.addSeparator()
        edit_action = menu.addAction("Code")
        render_action = menu.addAction("Render")

        action = menu.exec(self.main_window.cursor().pos())

        if action == open_action:
            self.on_title_label_left_clicked()

        elif action == edit_action:
            self.on_edit_button_clicked()

        elif action == render_action:
            self.on_render_button_clicked()

    def on_render_button_clicked(self,items=None):
        if not self.main_window.render_window:
            def render_window_on_finished():
                self.main_window.render_window.deleteLater()
                self.main_window.render_window = None
            if not items:
                items = {self.scenario_file.scenario_name:list(range(len(self.scenario_file.scripts_table)))}
            self.main_window.render_window = RenderWindow(self.main_window,items)
            self.main_window.render_window.finished.connect(render_window_on_finished)
            self.main_window.render_window.show()
        else:
            CFooter.broadcast("Rendering already in progress.", 2500)

    def on_edit_button_clicked(self):
        os.system(f'start "" "{self.scenario_file.scenario_path}"')

    def on_tab_widget_currentChanged(self, index):
        self.update_size_hint()
        i = self.tab_widget.currentIndex()
        self.project_cache["active_tab"] = self.tab_widget.tabText(self.tab_widget.currentIndex())

    # ---- Methods ----

    def update_size_hint(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None:
            self.tab_widget.setMinimumHeight(current_tab.sizeHint().height() + self.tab_widget.tabBar().height())
            self.tab_widget.updateGeometry()

    def populate(self):

        # ---------------------------------------------------------------------------

        hbox_layout = QHBoxLayout()

        self.title_label = CLabel(self.frame)
        self.title_label.setText(self.scenario_file.scenario_name)
        if self.project.project_cache['active_scenario_entry'] == self.scenario_file.scenario_name:
            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)
        self.title_label.left_clicked.connect(self.on_title_label_left_clicked)
        self.title_label.right_clicked.connect(self.on_title_label_right_clicked)
        hbox_layout.addWidget(self.title_label)

        self.edit_button = QPushButton("Code",self.frame)
        self.edit_button.setFixedWidth(75)
        self.edit_button.clicked.connect(self.on_edit_button_clicked)
        hbox_layout.addWidget(self.edit_button)

        self.render_button = QPushButton("Render",self.frame)
        self.render_button.setFixedWidth(75)
        self.render_button.clicked.connect(self.on_render_button_clicked)
        hbox_layout.addWidget(self.render_button)

        self.vbox_layout.addLayout(hbox_layout)

        # ---------------------------------------------------------------------------

        self.tab_widget = CTabWidget(self.main_window)
        self.tab_widget.tabBar().setMovable(False)

        if any([
                bool(self.scenario_file.vars_table),
                bool(self.scenario_file.vals_table),
                bool(self.scenario_file.errors_table.data),
            ]):

            self.tab_widget.setHidden(self.project_cache["is_closed"])

            if self.scenario_file.vars_table:
                self.scripts_table_view = CTableView(self.tab_widget, self.dictionary, self.scenario_file.scripts_table)
                self.scripts_table_view.resizeColumnsToContents()
                self.scripts_table_view.resizeRowsToContents()

                self.vars_table_view = CTableView(self.tab_widget, self.dictionary, self.scenario_file.vars_table)
                self.vars_table_view.resizeColumnsToContents()
                self.vars_table_view.resizeRowsToContents()

                self.vars_table_view.couple_sibling(self.scripts_table_view)
                self.scripts_table_view.couple_sibling(self.vars_table_view)

                def createContextMenu(table_view, position, index_at):
                    menu = QMenu(table_view)

                    selected_indices = table_view.selectedIndexes()

                    if any(index_at.row() == idx.row() for idx in selected_indices):
                        rows = [(row,) for row in {idx.row() for idx in selected_indices}]
                    else:
                        table_view.selectionModel().clearSelection()
                        rows = [(index_at.row(),)]

                    if len(rows)>1:
                        render_action = menu.addAction("Render Scripts")

                        menu.addSeparator()

                        delete_action = menu.addAction(f"Delete Scripts")
                        duplicate_action = menu.addAction(f"Duplicate Scripts")

                        row_above_action = menu.addAction(f"Insert Script Above Each")
                        row_below_action = menu.addAction(f"Insert Script Below Each")
                    else:
                        render_action = menu.addAction("Render Script")

                        menu.addSeparator()

                        delete_action = menu.addAction(f"Delete Script")
                        duplicate_action = menu.addAction(f"Duplicate Script")

                        row_above_action = menu.addAction(f"Insert Script Above")
                        row_below_action = menu.addAction(f"Insert Script Below")

                    n_rows_action = menu.addAction(f"Create N Scripts")

                    action = menu.exec(position)

                    if action == render_action:
                        items = {self.scenario_file.scenario_name:[row[0] for row in rows]}
                        self.on_render_button_clicked(items)
                    elif action == row_above_action:
                        table_view.table_model.insert_row(rows)
                    elif action == row_below_action:
                        rows = [(row+1,) for row,*_ in rows]
                        table_view.table_model.insert_row(rows)
                    elif action == n_rows_action:
                        num, ok = QInputDialog.getInt(table_view, "", "Number of rows:", 1, 1)
                        if ok:
                            length = table_view.table_model.rowCount()
                            self.vars_table_view.table_model.insert_row([(length+i,) for i in range(num)])
                    elif action == delete_action:
                        table_view.table_model.remove_row(rows)
                    elif action == duplicate_action:
                        table_view.table_model.duplicate_row(rows)

                    menu.deleteLater()

                    self.update_size_hint()

                self.vars_table_view.createContextMenu = createContextMenu
                self.scripts_table_view.createContextMenu = createContextMenu
            else:
                self.vars_table_view = QWidget(self.tab_widget)
                self.scripts_table_view = QWidget(self.tab_widget)

            self.tab_widget.addTab(self.scripts_table_view, "Names")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.scripts_table_view),
                                           bool(self.scenario_file.vars_table))

            self.tab_widget.addTab(self.vars_table_view, "Variables")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.vars_table_view),
                                           bool(self.scenario_file.vars_table))



            if self.scenario_file.vals_table:
                self.vals_table_view = CTableView(self.tab_widget, self.dictionary, self.scenario_file.vals_table)
                self.vals_table_view.resizeColumnsToContents()
                self.vals_table_view.resizeRowsToContents()
            else:
                self.vals_table_view = QWidget(self.tab_widget)

            self.tab_widget.addTab(self.vals_table_view, "Values")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.vals_table_view),
                                           bool(self.scenario_file.vals_table))


            if self.scenario_file.errors_table.data:
                self.errors_table_view = CErrorTableView(self.tab_widget, self.dictionary, self.scenario_file.errors_table)
                self.errors_table_view.resizeColumnsToContents()
                self.errors_table_view.resizeRowsToContents()
            else:
                self.errors_table_view = QWidget(self.tab_widget)

            self.tab_widget.addTab(self.errors_table_view, "Errors")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.errors_table_view),
                                           bool(self.scenario_file.errors_table.data))


            self.vbox_layout.addWidget(self.tab_widget)

            # ---------------------------------------------------------------------------
            active_tab_name = self.project_cache["active_tab"]
            tab_set = False

            if active_tab_name:
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == active_tab_name:
                        if self.tab_widget.isTabEnabled(i):
                            self.tab_widget.setCurrentIndex(i)
                            tab_set = True
                        break

            if not tab_set:
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.isTabEnabled(i):
                        self.tab_widget.setCurrentIndex(i)
                        tab_set = True
                        break

            if not tab_set:
                self.tab_widget.setCurrentIndex(3)

            self.update_size_hint()

        else:

            self.tab_widget.setHidden(True)

        self.tab_widget.currentChanged.connect(self.on_tab_widget_currentChanged)

        self.frame.recursive_install_event_filter()