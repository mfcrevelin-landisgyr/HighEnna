from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *

class TpyView:
    def __init__(self,tpy_file,dictionary):
        self.dictionary = {'tpy_view':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.project_cache = self.project.project_cache['tpyview'][tpy_file.tpy_file_name]
        self.project_cache.setdefault("is_closed",True)
        self.project_cache.setdefault("active_tab",None)

        self.tpy_file = tpy_file

        self.frame = CFrame()
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.clicked.connect(self.on_frame_clicked)
        self.vbox_layout = QVBoxLayout(self.frame)
        self.main_window.scroll_area_layout.addWidget(self.frame)
        self.populate()

    # ---- Slots ----

    def on_frame_clicked(self): 
        active_key = self.project.project_cache['active_tpy_entry']
        is_active = active_key == self.tpy_file.tpy_file_name
        is_closed = self.project_cache['is_closed']
        
        if any([
                not is_closed and is_active,
                is_closed and not is_active
            ]):
            return

        def update_menu(state):
            self.main_window.menu_widgets['File']['Save'].setEnabled(state)
            self.main_window.menu_widgets['File']['Render'].setEnabled(state)

        if is_closed:

            font = self.title_label.font()
            font.setBold(False)
            self.title_label.setFont(font)

            for key in sorted([key for key in self.main_window.tpy_views.keys() if key > self.tpy_file.tpy_file_name]):
                view = self.main_window.tpy_views[key]
                if not view.project_cache['is_closed']:
                    font = view.title_label.font()
                    font.setBold(True)
                    view.title_label.setFont(font)
                    self.project.project_cache['active_tpy_entry'] = key
                    update_menu(True)
                    return

            for key in sorted([key for key in self.main_window.tpy_views.keys() if key < self.tpy_file.tpy_file_name]):
                view = self.main_window.tpy_views[key]
                if not view.project_cache['is_closed']:
                    font = view.title_label.font()
                    font.setBold(True)
                    view.title_label.setFont(font)
                    self.project.project_cache['active_tpy_entry'] = key
                    update_menu(True)
                    return

            self.project.project_cache['active_tpy_entry'] = None
            update_menu(False)

        else:

            if active_key in self.main_window.tpy_views:
                active_tpy_entry = self.main_window.tpy_views[active_key]
                font = active_tpy_entry.title_label.font()
                font.setBold(False)
                active_tpy_entry.title_label.setFont(font)

            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)

            self.project.project_cache['active_tpy_entry'] = self.tpy_file.tpy_file_name
            update_menu(True)

    def on_title_label_left_clicked(self):
        if any([
                bool(self.tpy_file.vars_table),
                bool(self.tpy_file.vals_table),
                bool(self.tpy_file.errors_table.data),
            ]):

            new_val = not self.tab_widget.isHidden()
            self.tab_widget.setHidden(new_val)
            self.project_cache["is_closed"] = new_val
            self.on_frame_clicked()
        else:
            CToolTip(self.main_window, QCursor.pos(), "Nothing to edit")

    def on_title_label_right_clicked(self):
        self.on_frame_clicked()
        pass

    def on_render_button_clicked(self):
        pass

    def on_tab_widget_currentChanged(self, index):
        self.update_size_hint()
        self.project_cache["active_tab"] = self.tab_widget.tabText(self.tab_widget.currentIndex())

    # ---- Methods ----

    def update_size_hint(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None:
            hint = current_tab.sizeHint()
            max_height = int(self.main_window.height() * 3 / 4)
            target_height = min(hint.height() + self.tab_widget.tabBar().height(), max_height)
            self.tab_widget.setMinimumHeight(target_height)
            self.tab_widget.updateGeometry()

    def update_size_hint(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None:
            hint = current_tab.sizeHint()
            max_height = int(self.main_window.height() * 3 / 4)
            self.tab_widget.setMinimumHeight(hint.height() + self.tab_widget.tabBar().height())
            self.tab_widget.updateGeometry()

    def populate(self):

        # ---------------------------------------------------------------------------



        hbox_layout = QHBoxLayout()

        self.title_label = CLabel()
        self.title_label.setText(self.tpy_file.tpy_file_name)
        if self.project.project_cache['active_tpy_entry'] == self.tpy_file.tpy_file_name:
            font = self.title_label.font()
            font.setBold(True)
            self.title_label.setFont(font)
        hbox_layout.addWidget(self.title_label)

        self.render_button = QPushButton("Render")
        self.render_button.setFixedWidth(100)
        self.render_button.installEventFilter(self.frame)
        hbox_layout.addWidget(self.render_button)

        self.vbox_layout.addLayout(hbox_layout)

        # ---------------------------------------------------------------------------

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setMovable(False)
        self.tab_widget.installEventFilter(self.frame)
        self.tab_widget.tabBar().installEventFilter(self.frame)

        if any([
                bool(self.tpy_file.vars_table),
                bool(self.tpy_file.vals_table),
                bool(self.tpy_file.errors_table.data),
            ]):
        
            self.tab_widget.setHidden(self.project_cache["is_closed"])

            if self.tpy_file.vars_table:
                self.scripts_table_view = CTableView(self.dictionary, self.tpy_file.scripts_table)
                self.scripts_table_view.resizeColumnsToContents()
                self.scripts_table_view.resizeRowsToContents()
                self.scripts_table_view.installEventFilter(self.frame)

                self.vars_table_view = CTableView(self.dictionary, self.tpy_file.vars_table)
                self.vars_table_view.resizeColumnsToContents()
                self.vars_table_view.resizeRowsToContents()
                self.vars_table_view.installEventFilter(self.frame)

                def createVarsContextMenu(table_view, position, index_at):
                    menu = QMenu()

                    selected_indices = table_view.selectedIndexes()

                    if any(index_at.row() == idx.row() for idx in selected_indices):
                        rows = [(row,) for row in {idx.row() for idx in selected_indices}]
                    else:
                        table_view.selectionModel().clearSelection()
                        rows = [(index_at.row(),)]

                    if len(rows)>1:
                        delete_action = menu.addAction("Delete Rows")
                        duplicate_action = menu.addAction("Duplicate rows")

                        row_above_action = menu.addAction("Insert Row Above Each")
                        row_below_action = menu.addAction("Insert Row Below Each")
                    else:
                        delete_action = menu.addAction("Delete Row")
                        duplicate_action = menu.addAction("Duplicate row")

                        row_above_action = menu.addAction("Insert Row Above")
                        row_below_action = menu.addAction("Insert Row Below")

                    n_rows_action = menu.addAction("Add N Rows")

                    menu.addSeparator()

                    remove_obsolete_action = menu.addAction("Remove Obsolete")

                    action = menu.exec(position)

                    if action == row_above_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.insert_row(rows)
                    elif action == row_below_action:
                        rows = [(row+1,) for row,*_ in rows]
                        for table_view in table_view.siblings:
                            table_view.table_model.insert_row(rows)
                    elif action == n_rows_action:
                        num, ok = QInputDialog.getInt(table_view, "", "Number of rows:", 1, 1)
                        if ok:
                            length = table_view.table_model.rowCount()
                            for table_view in table_view.siblings:
                                table_view.table_model.insert_row([(length+i,) for i in range(num)])
                    elif action == delete_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.remove_row(rows)
                    elif action == duplicate_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.duplicate_row(rows)
                    elif action == remove_obsolete_action:
                        for table_view in table_view.siblings:
                            table_view.tpy_view.tpy_file.remove_obsolete()
                    
                    self.update_size_hint()

                def createScriptsContextMenu(table_view, position, index_at):
                    menu = QMenu()

                    selected_indices = table_view.selectedIndexes()

                    if any(index_at.row() == idx.row() for idx in selected_indices):
                        rows = [(row,) for row in {idx.row() for idx in selected_indices}]
                    else:
                        table_view.selectionModel().clearSelection()
                        rows = [(index_at.row(),)]

                    if len(rows)>1:
                        render_action = menu.addAction("Render Scripts")

                        menu.addSeparator()
                        
                        delete_action = menu.addAction("Delete Scripts")
                        duplicate_action = menu.addAction("Duplicate Scripts")

                        row_above_action = menu.addAction("Insert Script Above Each")
                        row_below_action = menu.addAction("Insert Script Below Each")
                    else:
                        render_action = menu.addAction("Render Script")

                        menu.addSeparator()
                        
                        delete_action = menu.addAction("Delete Script")
                        duplicate_action = menu.addAction("Duplicate Script")

                        row_above_action = menu.addAction("Insert Script Above")
                        row_below_action = menu.addAction("Insert Script Below")

                    n_rows_action = menu.addAction("Add N Scripts")

                    action = menu.exec(position)

                    if action == row_above_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.insert_row(rows)
                    elif action == row_below_action:
                        rows = [(row+1,) for row,*_ in rows]
                        for table_view in table_view.siblings:
                            table_view.table_model.insert_row(rows)
                    elif action == n_rows_action:
                        num, ok = QInputDialog.getInt(table_view, "", "Number of rows:", 1, 1)
                        if ok:
                            length = table_view.table_model.rowCount()
                            for table_view in table_view.siblings:
                                table_view.table_model.insert_row([(length+i,) for i in range(num)])
                    elif action == delete_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.remove_row(rows)
                    elif action == duplicate_action:
                        for table_view in table_view.siblings:
                            table_view.table_model.duplicate_row(rows)
                    
                    self.update_size_hint()

                self.vars_table_view.createContextMenu = createVarsContextMenu
                self.scripts_table_view.createContextMenu = createScriptsContextMenu

                self.vars_table_view.siblings.append(self.scripts_table_view)
                self.scripts_table_view.siblings.append(self.vars_table_view)
            else:
                self.vars_table_view = QWidget()
                self.scripts_table_view = QWidget()

            self.tab_widget.addTab(self.scripts_table_view, "Names")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.scripts_table_view),
                                           bool(self.tpy_file.vars_table))

            self.tab_widget.addTab(self.vars_table_view, "Variables")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.vars_table_view),
                                           bool(self.tpy_file.vars_table))



            if self.tpy_file.vals_table:
                self.vals_table_view = CTableView(self.dictionary, self.tpy_file.vals_table)
                self.vals_table_view.resizeColumnsToContents()
                self.vals_table_view.resizeRowsToContents()
                self.vals_table_view.installEventFilter(self.frame)
            else:
                self.vals_table_view = QWidget()

            self.tab_widget.addTab(self.vals_table_view, "Values")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.vals_table_view),
                                           bool(self.tpy_file.vals_table))


            if self.tpy_file.errors_table.data:
                self.errors_table_view = CErrorTableView(self.dictionary, self.tpy_file.errors_table)
                self.errors_table_view.resizeColumnsToContents()
                self.errors_table_view.resizeRowsToContents()
                self.errors_table_view.installEventFilter(self.frame)
            else:
                self.errors_table_view = QWidget()

            self.tab_widget.addTab(self.errors_table_view, "Errors")
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.errors_table_view),
                                           bool(self.tpy_file.errors_table.data))


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

        # ---------------------------------------------------------------------------

        self.title_label.left_clicked.connect(self.on_title_label_left_clicked)
        self.title_label.right_clicked.connect(self.on_title_label_right_clicked)
        self.render_button.clicked.connect(self.on_render_button_clicked)
        self.tab_widget.currentChanged.connect(self.on_tab_widget_currentChanged)