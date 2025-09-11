from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from custom_qt import *

class TpyView:
    def __init__(self,idx,tpy_file,dictionary):
        self.dictionary = {'tpyview':self}
        self.dictionary.update(dictionary)
        self.__dict__.update(self.dictionary)

        self.idx = idx
        self.tpy_file = tpy_file

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(2)
        self.vbox_layout = QVBoxLayout(frame)
        self.main_window.scroll_area_layout.addWidget(frame)
        self.populate()


    # ---- Slots ----

    def on_title_label_left_clicked(self):
        self.tab_widget.setHidden(not self.tab_widget.isHidden())
        if self.tab_widget.isHidden():
            self.main_window.open_entries.remove(self.tpy_file.tpy_file_name)
        else:
            self.main_window.open_entries.append(self.tpy_file.tpy_file_name)

    def on_title_label_right_clicked(self):
        pass

    def on_render_button_clicked(self):
        pass

    def on_tab_widget_currentChanged(self, index):
        current_tab = self.tab_widget.widget(index)
        if not current_tab:
            return

        hint = current_tab.sizeHint()

        self.tab_widget.setMinimumHeight(hint.height() + self.tab_widget.tabBar().height())

        # Force the frame to recompute
        self.tab_widget.updateGeometry()

    # ---- Methods ----

    def populate(self):
        # ---------------------------------------------------------------------------

        hbox_layout = QHBoxLayout()

        self.title_label = CLabel()
        self.title_label.setText(self.tpy_file.tpy_file_name)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)
        hbox_layout.addWidget(self.title_label)

        self.render_button = QPushButton("Render")
        self.render_button.setFixedWidth(100)
        hbox_layout.addWidget(self.render_button)

        self.vbox_layout.addLayout(hbox_layout)

        # # ---------------------------------------------------------------------------

        # self.line = QFrame()
        # self.line.setFrameShape(QFrame.Shape.HLine)
        # self.line.setHidden(True)
        # self.vbox_layout.addWidget(self.line)

        # ---------------------------------------------------------------------------

        self.tab_widget = QTabWidget()
        self.tab_widget.setHidden(self.tpy_file.tpy_file_name not in self.main_window.open_entries)

        if "errors_table" in self.tpy_file.__dict__:
            self.errors_table_view = CErrorTableView(self.dictionary, self.tpy_file.errors_table)
            self.tab_widget.addTab(self.errors_table_view, "Errors")
        else:
            if "vars_table" in self.tpy_file.__dict__:
                self.vars_table_view = CTableView(self.dictionary, self.tpy_file.vars_table)
                self.vars_table_view.resizeColumnsToContents()
                self.vars_table_view.resizeRowsToContents()
                self.tab_widget.addTab(self.vars_table_view, "Variables")

            if "vals_table" in self.tpy_file.__dict__:
                self.vals_table_view = CTableView(self.dictionary, self.tpy_file.vals_table)
                self.vals_table_view.resizeColumnsToContents()
                self.vals_table_view.resizeRowsToContents()
                self.tab_widget.addTab(self.vals_table_view, "Values")


        self.vbox_layout.addWidget(self.tab_widget)

        # ---------------------------------------------------------------------------

        self.title_label.left_clicked.connect(self.on_title_label_left_clicked)
        self.title_label.right_clicked.connect(self.on_title_label_right_clicked)
        self.render_button.clicked.connect(self.on_render_button_clicked)
        self.tab_widget.currentChanged.connect(self.on_tab_widget_currentChanged)

    def clear(self):
        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    _clear_layout(item.layout())
        _clear_layout(self.vbox_layout)
        self.entries.clear()
        self.open_entries.clear()

