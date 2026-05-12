"""Cross-platform terminal widget with PTY support."""
import logging
import re

logger = logging.getLogger(__name__)
import sys
import select as selector
import threading
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QThread, Signal
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
# 232-255: grayscale — pre-computed as literals (range(8, 240, 10) = 8,18,…,238)
] + [
    "#080808", "#121212", "#1C1C1C", "#262626", "#303030", "#3A3A3A",
    "#444444", "#4E4E4E", "#585858", "#626262", "#6C6C6C", "#767676",
    "#808080", "#8A8A8A", "#949494", "#9E9E9E", "#A8A8A8", "#B2B2B2",
    "#BCBCBC", "#C6C6C6", "#D0D0D0", "#DADADA", "#E4E4E4", "#EEEEEE",
]

# ANSI SGR foreground/background lookup tables
_STD_FG: dict[str, str] = {
    "30": "#000000", "31": "#CC0000", "32": "#4E9A06", "33": "#C4A000",
    "34": "#3465A4", "35": "#75517B", "36": "#06989A", "37": "#FFFFFF",
}
_BRIGHT_FG: dict[str, str] = {
    "90": "#555555", "91": "#F2777A", "92": "#9FD900", "93": "#FEE12B",
    "94": "#6CB6FF", "95": "#D397EE", "96": "#8BD9CA", "97": "#FFFFFF",
}
_STD_BG: dict[str, str] = {
    "40": "#000000", "41": "#CC0000", "42": "#4E9A06", "43": "#C4A000",
    "44": "#3465A4", "45": "#75517B", "46": "#06989A", "47": "#FFFFFF",
}
# SGR 100-107: bright background (ISO 8613-6 / ECMA-48)
# Maps to the same palette as _BRIGHT_FG (bright foreground) per spec
_BRIGHT_BG: dict[str, str] = {
    "100": "#555555", "101": "#F2777A", "102": "#9FD900", "103": "#FEE12B",
    "104": "#6CB6FF", "105": "#D397EE", "106": "#8BD9CA", "107": "#FFFFFF",
}

# Pre-compiled: ANSI SGR escape sequence splitter — hot path, called on every PTY output batch
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


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
                proc = self._process
            master_fd = proc.master_fd
            if master_fd is not None:
                # Linux/macOS/BSD/Solaris — use select() on PTY master fd
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
                    logger.warning("PtyReader select error: %s", e, exc_info=True)
                    break
            else:
                # winpty path (Windows) — no fd-based select, poll with short sleep to avoid CPU spin
                try:
                    data = proc.read()
                    if data:
                        self.output_ready.emit(data)
                except (OSError, ValueError, RuntimeError, AttributeError) as e:
                    # AttributeError: _winpty_process was set to None by cleanup()
                    # racing between proc capture and read() call
                    logger.error("PtyReader read error (winpty): %s", e, exc_info=True)
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
        parts = _ANSI_ESCAPE_RE.split(text)
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
                    elif code in _STD_FG:
                        current_format.setForeground(QColor(_STD_FG[code]))
                    elif code == "39":
                        current_format.setForeground(default_format.foreground())
                    # ── Bright foreground (90-97) ─────────────────────────────
                    elif code in _BRIGHT_FG:
                        current_format.setForeground(QColor(_BRIGHT_FG[code]))
                    # ── Standard background (40-47, 49) ───────────────────────
                    elif code in _STD_BG:
                        current_format.setBackground(QColor(_STD_BG[code]))
                    elif code == "49":
                        current_format.setBackground(default_format.background())
                    # ── Bright background (100-107) ────────────────────────────
                    elif code in _BRIGHT_BG:
                        current_format.setBackground(QColor(_BRIGHT_BG[code]))
                    # ── Extended foreground: 38;5;N (256-color) or 38;2;R;G;B (24-bit)
                    elif code == "38":
                        if i < len(codes):
                            mode = codes[i]
                            i += 1
                            if mode == "5" and i < len(codes):
                                try:
                                    color_idx = int(codes[i])
                                except ValueError:
                                    logger.warning("ANSI parser: malformed 256-color foreground code %r at pos %d", codes[i], i, exc_info=True)
                                    i += 1
                                    continue
                                if 0 <= color_idx < len(_xterm256):
                                    current_format.setForeground(QColor(_xterm256[color_idx]))
                                i += 1
                            elif mode == "2" and i + 2 < len(codes):
                                try:
                                    r, g, b = int(codes[i]), int(codes[i + 1]), int(codes[i + 2])
                                except ValueError:
                                    logger.warning("ANSI parser: malformed 24-bit foreground RGB %r/%r/%r at pos %d", codes[i], codes[i+1], codes[i+2], i, exc_info=True)
                                    i += 3
                                    continue
                                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                                    logger.warning("ANSI parser: 24-bit foreground RGB out of range (%d,%d,%d) at pos %d", r, g, b, i, exc_info=True)
                                    i += 3
                                    continue
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
                                    logger.warning("ANSI parser: malformed 256-color background code %r at pos %d", codes[i], i, exc_info=True)
                                    i += 1
                                    continue
                                if 0 <= color_idx < len(_xterm256):
                                    current_format.setBackground(QColor(_xterm256[color_idx]))
                                i += 1
                            elif mode == "2" and i + 2 < len(codes):
                                try:
                                    r, g, b = int(codes[i]), int(codes[i + 1]), int(codes[i + 2])
                                except ValueError:
                                    logger.warning("ANSI parser: malformed 24-bit background RGB %r/%r/%r at pos %d", codes[i], codes[i+1], codes[i+2], i, exc_info=True)
                                    i += 3
                                    continue
                                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                                    logger.warning("ANSI parser: 24-bit background RGB out of range (%d,%d,%d) at pos %d", r, g, b, i, exc_info=True)
                                    i += 3
                                    continue
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
            modifiers = event.modifiers()

            # Guard: skip write if process is closed (same check as write_input)
            if not self._process or self._process.is_closed:
                return True

            # ── Control combos ───────────────────────────────────────────────
            if key == Qt.Key_C and modifiers & Qt.ControlModifier:
                self._process.write("\x03")
                return True
            elif key == Qt.Key_V and modifiers & Qt.ControlModifier:
                clipboard = QApplication.clipboard()
                if clipboard:
                    text = clipboard.text()
                    if text:
                        self._process.write(text)
                return True

            # ── Escape sequences for navigation / editing ─────────────────────
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
            elif key == Qt.Key_Escape:
                self._process.write("\x1b")
                return True

            # ── Arrow keys → ANSI escape sequences ────────────────────────────
            elif key == Qt.Key_Up:
                self._process.write("\x1b[A")
                return True
            elif key == Qt.Key_Down:
                self._process.write("\x1b[B")
                return True
            elif key == Qt.Key_Right:
                self._process.write("\x1b[C")
                return True
            elif key == Qt.Key_Left:
                self._process.write("\x1b[D")
                return True

            # ── Home / End / PageUp / PageDown ────────────────────────────────
            elif key == Qt.Key_Home:
                self._process.write("\x1b[H")
                return True
            elif key == Qt.Key_End:
                self._process.write("\x1b[F")
                return True
            elif key == Qt.Key_PageUp:
                self._process.write("\x1b[5~")
                return True
            elif key == Qt.Key_PageDown:
                self._process.write("\x1b[6~")
                return True

            # ── Forward printable characters ───────────────────────────────────
            elif event.text():
                char = event.text()
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
