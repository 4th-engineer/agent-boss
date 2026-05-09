"""Pixel avatar overlay for terminals."""
import json
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QFont


DEFAULT_AVATAR = "beaver"


class AvatarOverlay(QWidget):
    """Pixel art avatar displayed over terminal."""

    def __init__(self, parent=None, avatar_id: str = DEFAULT_AVATAR):
        super().__init__(parent)
        self._avatar_id = avatar_id
        self._sprite = []
        self._colors = {}
        self._avatar_data = {}
        self._load_avatar(avatar_id)

        # Position: bottom-right corner
        self._offset_x = -8
        self._offset_y = -8

        self.setFixedSize(80, 80)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _load_avatar(self, avatar_id: str):
        """Load avatar data from JSON."""
        path = Path(__file__).parent / "avatars" / "avatars.json"
        try:
            with open(path) as f:
                data = json.load(f)
                if avatar_id in data:
                    self._avatar_id = avatar_id
                    self._avatar_data = data[avatar_id]
                    self._sprite = self._avatar_data.get("sprite", [])
                    self._colors = self._avatar_data.get("colors", {})
                    return
        except Exception as e:
            print(f"Failed to load avatar {avatar_id}: {e}")

        # Fallback to default avatar
        if avatar_id != DEFAULT_AVATAR:
            self._load_avatar(DEFAULT_AVATAR)

    def set_avatar(self, avatar_id: str):
        """Change to a different avatar."""
        if avatar_id != self._avatar_id:
            self._load_avatar(avatar_id)
            self.update()

    def get_avatar_id(self) -> str:
        return self._avatar_id

    def paintEvent(self, event):
        """Draw the pixel art avatar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        if not self._sprite:
            return

        # Calculate pixel size to fit sprite in widget
        rows = len(self._sprite)
        cols = len(self._sprite[0]) if rows > 0 and self._sprite[0] else 1
        if rows == 0 or cols == 0 or self.width() == 0 or self.height() == 0:
            return
        cell_w = max(self.width() // max(cols, 1), 1)
        cell_h = max(self.height() // max(rows, 1), 1)
        pixel_size = min(cell_w, cell_h, 12)
        if pixel_size <= 0:
            return

        # Center the sprite
        total_w = cols * pixel_size
        total_h = rows * pixel_size
        x_offset = (self.width() - total_w) // 2
        y_offset = (self.height() - total_h) // 2

        for r, row in enumerate(self._sprite):
            for c, char in enumerate(row):
                if char == ' ':
                    continue
                color = self._get_color_for_char(char)
                x = x_offset + c * pixel_size
                y = y_offset + r * pixel_size
                painter.fillRect(x, y, pixel_size - 1, pixel_size - 1, color)

        # Draw name label below
        name = self._avatar_data.get("name", "")
        if name:
            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Monospace", 7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter, name)

    def _get_color_for_char(self, char: str) -> QColor:
        """Map sprite character to a color."""
        color_map = {
            '█': self._colors.get('primary', '#FFFFFF'),
            '░': self._colors.get('secondary', '#888888'),
            '▒': self._colors.get('accent', '#FFFF00'),
            '▓': self._colors.get('primary', '#FFFFFF'),
            '◐': self._colors.get('accent', '#4CAF50'),
            '◑': self._colors.get('accent', '#4CAF50'),
            '▀': self._colors.get('primary', '#FFFFFF'),
            '▄': self._colors.get('secondary', '#888888'),
        }
        return QColor(color_map.get(char, '#FFFFFF'))

    def reposition(self, parent_rect):
        """Reposition to bottom-right of parent."""
        # Use parent dimensions for relative positioning
        self.move(
            parent_rect.width() + self._offset_x - self.width(),
            parent_rect.height() + self._offset_y - self.height()
        )


def list_avatars() -> list[dict]:
    """Return list of available avatars."""
    path = Path(__file__).parent / "avatars" / "avatars.json"
    try:
        with open(path) as f:
            data = json.load(f)
            return [{"id": k, **v} for k, v in data.items()]
    except (json.JSONDecodeError, OSError):
        return []
