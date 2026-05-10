"""Cross-platform terminal widget with PTY support."""
import logging
import re

logger = logging.getLogger(__name__)
import sys
import select as selector
import threading
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QThread, Signal, Property
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QKeyEvent

from agent_boss.process_manager import PtyProcess
from agent_boss.avatar_overlay import AvatarOverlay


# ── xterm 256-color palette (ISO 8613-6 / ECMA-48) ──────────────────────────
# Index 0-15:   standard 16 ANSI colors
# Index 16-231: 6×6×6 RGB cube (216 colors: 16 + 36×6)
# Index 232-255: 24 grayscale (black → white)
_xterm256: list[str] = [
    # 0-7: standard
    "#000000", "#CC0000", "#4E9A06", "#C4A000",
    "#3465A4", "#75517B", "#06989A", "#FFFFFF",
    # 8-15: bright
    "#555555", "#F2777A", "#9FD900", "#FEE12B",
    "#6CB6FF", "#D397EE", "#8BD9CA", "#FFFFFF",
    # 16-231: RGB cube
] + [
    f"#{r:02x}{g:02x}{b:02x}"
    for r in (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)
    for g in (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)
    for b in (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)
# 232-255: grayscale (24 colors: 0x08..0xEE, step 10)
] + [f"#{i:02x}{i:02x}{i:02x}" for i in range(8, 0xF0, 10)]


class PtyReader(QThread):
    """Reads PTY output in background thread."""

    output_ready = Signal(str)

    def __init__(self, process: PtyProcess):
        super().__init__()
        self._process = process
        self._running = False
        self._lock = threading.Lock()

    def run(self):
        self._running = True
        while self._running:
            with self._lock:
                if self._process is None or self._process.is_closed:
                    break
            if sys.platform in ("linux", "darwin"):
                master_fd = self._process.master_fd
                if master_fd is not None:
                    try:
                        ready, _, _ = selector.select([master_fd], [], [], 0.05)
                        if ready:
                            with self._lock:
                                if self._process is None or self._process.is_closed:
                                    break
                                proc = self._process
                            data = proc.read()
                            if data:
                                self.output_ready.emit(data)
                        # Check if process closed during select
                        with self._lock:
                            if self._process is None or self._process.is_closed:
                                break
                    except (OSError, ValueError, RuntimeError) as e:
                        # Unexpected error in selector - process may have closed
                        logger.warning("PtyReader select error: %s", e)
                        break
            else:
                # Fallback for other platforms (e.g. other Unix, or Windows with winpty)
                with self._lock:
                    if self._process is None or self._process.is_closed:
                        break
                    proc = self._process
                master_fd = proc.master_fd
                if master_fd is not None:
                    try:
                        ready, _, _ = selector.select([master_fd], [], [], 0.05)
                        if ready:
                            data = proc.read()
                            if data:
                                self.output_ready.emit(data)
                    except (OSError, ValueError, RuntimeError) as e:
                        logger.warning("PtyReader select error: %s", e)
                        break
                else:
                    # winpty path - no fd-based select, poll with short sleep to avoid CPU spin
                    try:
                        data = proc.read()
                        if data:
                            self.output_ready.emit(data)
                    except (OSError, ValueError, RuntimeError) as e:
                        logger.warning("PtyReader read error (winpty): %s", e)
                        break
                    QThread.msleep(50)

    def stop(self):
        with self._lock:
            self._running = False


class TerminalWidget(QWidget):
    """Terminal emulator widget with ANSI color support."""

    def __init__(self, process: PtyProcess, parent=None, avatar_id: str = "beaver"):
        super().__init__(parent)
        self._process = process
        self._avatar_id = avatar_id
        self._setup_ui()
        self._start_reader()
        self._setup_avatar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("Monospace", 10))
        self._text_edit.setStyleSheet("""
            QTextEdit { background-color: #1E1E1E; color: #D4D4D4; border: none; }
        """)
        self._text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text_edit.document().setMaximumBlockCount(10000)
        self._text_edit.installEventFilter(self)

        layout.addWidget(self._text_edit)

        # Avatar overlay
        self._avatar = AvatarOverlay(self, self._avatar_id)
        self._avatar.hide()  # Hidden by default, toggle with method

    def _setup_avatar(self):
        """Position avatar in corner."""
        # Will be repositioned when terminal is shown
        pass

    def resizeEvent(self, event):
        """Reposition avatar when terminal resizes."""
        super().resizeEvent(event)
        if hasattr(self, '_avatar'):
            self._avatar.reposition(self.rect())

    def show_avatar(self):
        """Show the avatar overlay."""
        if hasattr(self, '_avatar'):
            self._avatar.reposition(self.rect())
            self._avatar.show()

    def hide_avatar(self):
        """Hide the avatar overlay."""
        if hasattr(self, '_avatar'):
            self._avatar.hide()

    def toggle_avatar(self):
        """Toggle avatar visibility."""
        if hasattr(self, '_avatar'):
            if self._avatar.isVisible():
                self.hide_avatar()
            else:
                self.show_avatar()

    def set_avatar(self, avatar_id: str):
        """Change the avatar."""
        self._avatar_id = avatar_id
        if hasattr(self, '_avatar'):
            self._avatar.set_avatar(avatar_id)

    def get_avatar_id(self) -> str:
        """Get current avatar ID."""
        return self._avatar_id

    def is_avatar_visible(self) -> bool:
        """Check if avatar overlay is visible."""
        return self._avatar.isVisible()

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
                codes_str = part[2:-1]
                codes = codes_str.split(";") if codes_str else ["0"]
                i = 0
                while i < len(codes):
                    code = codes[i]
                    i += 1
                    # ── Reset ──────────────────────────────────────────────
                    if code == "0":
                        current_format = QTextCharFormat(default_format)
                        current_format.setBackground(default_format.background())
                    # ── Bold / Dim / Italic / Underline / Blink ──────────────
                    elif code == "1":
                        fg = current_format.foreground().color()
                        current_format.setForeground(fg.lighter(150))
                    elif code == "2":
                        fg = current_format.foreground().color()
                        current_format.setForeground(fg.darker(150))
                    elif code == "3":
                        current_format.setFontItalic(True)
                    elif code == "4":
                        current_format.setFontUnderline(True)
                    elif code == "5":
                        pass  # slow blink – no effect in plain text
                    elif code == "6":
                        pass  # rapid blink – no effect in plain text
                    # ── Reverse / Conceal / Strike ───────────────────────────
                    elif code == "7":
                        fg = current_format.foreground().color()
                        bg = current_format.background().color()
                        current_format.setForeground(bg)
                        current_format.setBackground(fg)
                    elif code == "8":
                        bg = current_format.background().color()
                        current_format.setForeground(bg)
                    elif code == "9":
                        current_format.setFontStrikeOut(True)
                    # ── Bold/Dim/Italic/Underline/Blink/Reverse/Conceal/Strike OFF
                    elif code == "22":
                        current_format.setForeground(default_format.foreground())
                    elif code == "23":
                        current_format.setFontItalic(default_format.fontItalic())
                    elif code == "24":
                        current_format.setFontUnderline(default_format.fontUnderline())
                    elif code == "25":
                        pass  # blink off
                    elif code == "27":
                        current_format.setForeground(default_format.foreground())
                        current_format.setBackground(default_format.background())
                    elif code == "28":
                        current_format.setForeground(default_format.foreground())
                    elif code == "29":
                        current_format.setFontStrikeOut(default_format.fontStrikeOut())
                    # ── Standard foreground (30-37, 39) ───────────────────────
                    elif code == "30": current_format.setForeground(QColor("#000000"))
                    elif code == "31": current_format.setForeground(QColor("#CC0000"))
                    elif code == "32": current_format.setForeground(QColor("#4E9A06"))
                    elif code == "33": current_format.setForeground(QColor("#C4A000"))
                    elif code == "34": current_format.setForeground(QColor("#3465A4"))
                    elif code == "35": current_format.setForeground(QColor("#75517B"))
                    elif code == "36": current_format.setForeground(QColor("#06989A"))
                    elif code == "37": current_format.setForeground(QColor("#FFFFFF"))
                    elif code == "39": current_format.setForeground(default_format.foreground())
                    # ── Bright foreground (90-97) ─────────────────────────────
                    elif code == "90": current_format.setForeground(QColor("#555555"))
                    elif code == "91": current_format.setForeground(QColor("#F2777A"))
                    elif code == "92": current_format.setForeground(QColor("#9FD900"))
                    elif code == "93": current_format.setForeground(QColor("#FEE12B"))
                    elif code == "94": current_format.setForeground(QColor("#6CB6FF"))
                    elif code == "95": current_format.setForeground(QColor("#D397EE"))
                    elif code == "96": current_format.setForeground(QColor("#8BD9CA"))
                    elif code == "97": current_format.setForeground(QColor("#FFFFFF"))
                    # ── Standard background (40-47, 49) ───────────────────────
                    elif code == "40": current_format.setBackground(QColor("#000000"))
                    elif code == "41": current_format.setBackground(QColor("#CC0000"))
                    elif code == "42": current_format.setBackground(QColor("#4E9A06"))
                    elif code == "43": current_format.setBackground(QColor("#C4A000"))
                    elif code == "44": current_format.setBackground(QColor("#3465A4"))
                    elif code == "45": current_format.setBackground(QColor("#75517B"))
                    elif code == "46": current_format.setBackground(QColor("#06989A"))
                    elif code == "47": current_format.setBackground(QColor("#FFFFFF"))
                    elif code == "49": current_format.setBackground(default_format.background())
                    # ── Extended foreground: 38;5;N (256-color) or 38;2;R;G;B (24-bit)
                    elif code == "38":
                        if i < len(codes):
                            mode = codes[i]
                            i += 1
                            if mode == "5" and i < len(codes):
                                try:
                                    color_idx = int(codes[i])
                                except ValueError:
                                    i += 1
                                    continue
                                if 0 <= color_idx < len(_xterm256):
                                    current_format.setForeground(QColor(_xterm256[color_idx]))
                                i += 1
                            elif mode == "2" and i + 2 < len(codes):
                                r, g, b = int(codes[i]), int(codes[i + 1]), int(codes[i + 2])
                                i += 3
                                current_format.setForeground(QColor(r, g, b))
                    # ── Extended background: 48;5;N or 48;2;R;G;B ───────────
                    elif code == "48":
                        if i < len(codes):
                            mode = codes[i]
                            i += 1
                            if mode == "5" and i < len(codes):
                                try:
                                    color_idx = int(codes[i])
                                except ValueError:
                                    i += 1
                                    continue
                                if 0 <= color_idx < len(_xterm256):
                                    current_format.setBackground(QColor(_xterm256[color_idx]))
                                i += 1
                            elif mode == "2" and i + 2 < len(codes):
                                r, g, b = int(codes[i]), int(codes[i + 1]), int(codes[i + 2])
                                i += 3
                                current_format.setBackground(QColor(r, g, b))
            else:
                if part and part.strip():
                    cursor.setCharFormat(current_format)
                    cursor.insertText(part)

    def eventFilter(self, obj, event):
        """Handle key events for terminal input."""
        if obj == self._text_edit and isinstance(event, QKeyEvent):
            key = event.key()
            if key == Qt.Key_Escape:
                # Allow escape to bubble up (e.g., to clear selection)
                pass
            elif key == Qt.Key_Return:
                self._process.write("\n")
                return True
            elif key == Qt.Key_Backspace:
                self._process.write("\x7f")
                return True
            elif key == Qt.Key_Tab:
                self._process.write("\t")
                return True
            elif key == Qt.Key_Delete:
                self._process.write("\x1b[3~")
                return True
            elif key == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
                self._process.write("\x03")
                return True
            elif key == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
                clipboard = QApplication.clipboard()
                if clipboard:
                    text = clipboard.text()
                    if text:
                        self._process.write(text)
                return True
            elif event.text():
                char = event.text()
                # Forward printable characters and common control sequences
                # Only block internal Qt sequences, let terminals handle Unicode
                if char and not char.iscntrl():
                    self._process.write(char)
                    return True
                # Allow common control chars that terminals need
                if char in ('\x01', '\x02', '\x05', '\x06'):
                    self._process.write(char)
                    return True
        return super().eventFilter(obj, event)

    def write_input(self, text: str):
        """Write text input to the PTY process."""
        if self._process and not self._process.is_closed:
            self._process.write(text)

    def cleanup(self):
        if hasattr(self, "_reader"):
            self._reader.stop()
            if not self._reader.wait(1500):
                self._reader.terminate()
                # Ensure thread terminates after forceful termination
                if not self._reader.wait(500):
                    logger.warning("PtyReader thread did not terminate cleanly")
            self._reader.deleteLater()
            del self._reader
        if self._process:
            self._process.close()
            self._process = None
        # Note: QWidget has no cleanup() method — do not call super().cleanup()
