"""Cross-platform terminal widget with PTY support."""
import re
import sys
import select as selector
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QKeyEvent

from agent_boss.process_manager import PtyProcess


class PtyReader(QThread):
    """Reads PTY output in background thread."""

    output_ready = Signal(str)

    def __init__(self, process: PtyProcess):
        super().__init__()
        self._process = process
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            if self._process and not self._process.is_closed:
                if sys.platform == "linux" or sys.platform == "darwin":
                    try:
                        ready, _, _ = selector.select([self._process._fd], [], [], 0.05)
                        if ready:
                            data = self._process.read()
                            if data:
                                self.output_ready.emit(data)
                    except (OSError, ValueError):
                        pass
                else:
                    data = self._process.read()
                    if data:
                        self.output_ready.emit(data)
                    QThread.msleep(50)
            else:
                QThread.msleep(50)

    def stop(self):
        self._running = False


class TerminalWidget(QWidget):
    """Terminal emulator widget with ANSI color support."""

    def __init__(self, process: PtyProcess, parent=None):
        super().__init__(parent)
        self._process = process
        self._setup_ui()
        self._start_reader()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("Consolas", 10))
        self._text_edit.setStyleSheet("""
            QTextEdit { background-color: #1E1E1E; color: #D4D4D4; border: none; }
        """)
        self._text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text_edit.document().setMaximumBlockCount(10000)
        self._text_edit.installEventFilter(self)

        layout.addWidget(self._text_edit)

    def _start_reader(self):
        self._reader = PtyReader(self._process)
        self._reader.output_ready.connect(self._append_output)
        self._reader.start()

    def _append_output(self, data: str):
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._parse_and_insert(cursor, data)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    def _parse_and_insert(self, cursor, text: str):
        """Parse ANSI escape sequences and insert styled text."""
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#D4D4D4"))
        parts = re.split(r"(\x1b\[[0-9;]*m)", text)
        current_format = QTextCharFormat(default_format)

        for part in parts:
            if part.startswith("\x1b["):
                codes = part[2:-1].split(";") if part[2:-1] else ["0"]
                for code in codes:
                    if code == "0":
                        current_format = QTextCharFormat(default_format)
                    elif code == "1":
                        fg = current_format.foreground().color()
                        current_format.setForeground(fg.lighter(150))
                    elif code == "30": current_format.setForeground(QColor("#000000"))
                    elif code == "31": current_format.setForeground(QColor("#CC0000"))
                    elif code == "32": current_format.setForeground(QColor("#4E9A06"))
                    elif code == "33": current_format.setForeground(QColor("#C4A000"))
                    elif code == "34": current_format.setForeground(QColor("#3465A4"))
                    elif code == "35": current_format.setForeground(QColor("#75517B"))
                    elif code == "36": current_format.setForeground(QColor("#06989A"))
                    elif code == "37": current_format.setForeground(QColor("#FFFFFF"))
                    elif code == "90": current_format.setForeground(QColor("#555555"))
                    elif code == "91": current_format.setForeground(QColor("#F2777A"))
                    elif code == "92": current_format.setForeground(QColor("#9FD900"))
                    elif code == "93": current_format.setForeground(QColor("#FEE12B"))
                    elif code == "94": current_format.setForeground(QColor("#6CB6FF"))
                    elif code == "95": current_format.setForeground(QColor("#D397EE"))
                    elif code == "96": current_format.setForeground(QColor("#8BD9CA"))
                    elif code == "97": current_format.setForeground(QColor("#FFFFFF"))
            else:
                if part:
                    cursor.setCharFormat(current_format)
                    cursor.insertText(part)

    def eventFilter(self, obj, event):
        """Handle key events for terminal input."""
        if obj == self._text_edit and isinstance(event, QKeyEvent):
            if event.key() == 0x100:  # Return
                self._process.write("\n")
                return True
            elif event.key() == 0x103:  # Backtab
                self._process.write("\t")
                return True
            elif event.key() == 0x7F:  # Backspace
                self._process.write("\x7f")
                return True
            elif event.key() == 0x43 and event.modifiers() == 0x140000:  # Ctrl+C
                self._process.write("\x03")
                return True
            elif event.text():
                char = event.text()
                if ord(char) >= 32:
                    self._process.write(char)
                return True
        return super().eventFilter(obj, event)

    def write_input(self, text: str):
        if self._process:
            self._process.write(text)

    def cleanup(self):
        if hasattr(self, "_reader"):
            self._reader.stop()
            self._reader.wait(1000)
