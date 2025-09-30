from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont, QColor, QTextCharFormat, QTextCursor

from custom_qt import CProgressBar

class RenderWorker(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(bool)
    append_text_signal = pyqtSignal(str)

    def __init__(self, parent, queue):
        super().__init__(parent)
        self.parent = parent
        self.queue = queue
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        all_ok = True
        for file_name, items in self.queue.items():
            if self._stop_requested:
                break
            all_ok &= self.parent.project.tpy_files[file_name].render(
                    items,
                    self.append_text_signal,
                    self.progress_signal
                )
        self.result_signal.emit(all_ok)

class RenderWindow(QDialog):
    closed = pyqtSignal()

    def __init__(self, parent, queue):
        super().__init__(parent)
        self.parent = parent

        self.queue = queue
        self.total_steps = sum(len(items) for items in queue.values())
        self.current_step = 0

        self.text_monitor = QTextEdit(self)
        self.text_monitor.setReadOnly(True)
        self.text_monitor.setFontFamily("Liberation Mono")
        self.text_monitor.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        char_format = QTextCharFormat()
        char_format.setForeground(QColor("white"))
        cursor = self.text_monitor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(char_format)

        self.progress_bar = CProgressBar(self)
        self.progress_bar.setRange(0, self.total_steps)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFormat("%p%")

        layout = QVBoxLayout()
        layout.addWidget(self.text_monitor)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.setWindowTitle("Rendering")
        self.adjust_size()

        self.worker = RenderWorker(parent, queue)
        self.worker.append_text_signal.connect(self.append_to_monitor)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.handle_completion)
        self.worker.start()

    def append_to_monitor(self,text):
        text = "<pre style='font-family: Liberation Mono;'>{text}</pre>".format(text=text.replace('\n','<br>'))
        self.text_monitor.insertHtml(text)

    def update_progress(self,n):
        self.current_step += n
        self.progress_bar.setValue(self.current_step)
        self.parent.populate()

    def handle_completion(self, all_ok: bool):
        pass
        # if all_ok:
            # QTimer.singleShot(750, self.close)

    def adjust_size(self):
        numer, denom = 4, 8

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if not screen:
            screen = QApplication.primaryScreen()

        available_geometry = screen.availableGeometry()

        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        new_width = screen_width * numer // denom
        new_height = screen_height * numer // denom

        new_x = available_geometry.x() + (screen_width - new_width) // 2
        new_y = available_geometry.y() + (screen_height - new_height) // 2

        self.setGeometry(new_x, new_y, new_width, new_height)

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.wait(1000)
        self.closed.emit()
        super().closeEvent(event)
