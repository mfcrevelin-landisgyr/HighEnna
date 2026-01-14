from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, QMutex, QMutexLocker, pyqtSignal
from PyQt6.QtGui import QCursor, QFont, QColor, QTextCharFormat, QTextCursor

from custom_qt import CProgressBar

import time

class RenderWorker(QThread):
    result_signal = pyqtSignal(bool)
    
    def __init__(self, parent,
                work_queue,
                enqueueu_message,
                tick_progress
            ):
        super().__init__(parent)
        self.parent = parent
        self.work_queue = work_queue
        self.enqueueu_message = enqueueu_message
        self.tick_progress = tick_progress

        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        all_ok = True
        for file_name, items in self.work_queue.items():
            if self._stop_requested:
                break
            all_ok &= self.parent.project.scenario_files[file_name].render(
                    items,
                    self.enqueueu_message,
                    self.tick_progress
                )
        self.result_signal.emit(all_ok)

class PublishWorker(QThread):
    publish_progress = pyqtSignal()

    def __init__(self, parent,):
        super().__init__(parent)
        self.parent = parent
        self._stop_requested = False
        self.stale_time_ms = 10

    def stop(self):
        self._stop_requested = True

    def run(self):
        while not self._stop_requested:
            self.publish_progress.emit()
            self.msleep(self.stale_time_ms)
        self.msleep(self.stale_time_ms)
        self.publish_progress.emit()

class RenderWindow(QDialog):
    closed = pyqtSignal()

    def __init__(self, parent, work_queue):
        super().__init__(parent)
        self.parent = parent

        self.total_steps = sum(len(items) for items in work_queue.values())
        self.current_step = 0
        self.message_buffer = []

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
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFormat("%p%")

        layout = QVBoxLayout()
        layout.addWidget(self.text_monitor)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.setWindowTitle("Rendering Monitor")
        self.adjust_size()

        self.worker_lock = QMutex()

        self.publisher = PublishWorker(parent)
        self.publisher.publish_progress.connect(self.publish_progress)
        self.renderer = RenderWorker(parent, work_queue, 
                self.enqueueu_message,
                self.tick_progress
            )
        self.renderer.result_signal.connect(self.handle_completion)
        
        self.publisher.start()
        self.renderer.start()

    def enqueueu_message(self, text):
        with QMutexLocker(self.worker_lock):
            self.message_buffer.append(text)

    def tick_progress(self, n):
        with QMutexLocker(self.worker_lock):
            self.current_step += n

    def publish_progress(self):
        with QMutexLocker(self.worker_lock):
            text = "<pre style='font-family: Liberation Mono;'>{text}</pre>".format(text=(''.join(self.message_buffer)).replace('\n','<br>'))
            self.text_monitor.insertHtml(text)
            self.message_buffer.clear()
            self.progress_bar.setValue(self.current_step)

    def handle_completion(self, all_ok: bool):
        self.publisher.stop()
        self.parent.populate()
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
        self.renderer.stop()
        self.renderer.wait(1000)
        self.closed.emit()
        super().closeEvent(event)
