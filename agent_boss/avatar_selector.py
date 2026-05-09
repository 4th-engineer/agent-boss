"""Avatar selector dialog."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, QScrollArea, QWidget
from PySide6.QtCore import Signal
from agent_boss.avatar_overlay import list_avatars


class AvatarSelector(QDialog):
    """Dialog to select an avatar for a terminal."""

    avatar_selected = Signal(str)

    def __init__(self, parent=None, current_avatar=None):
        super().__init__(parent)
        self._current = current_avatar or "beaver"
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Select Avatar")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        title = QLabel("Choose an avatar for this terminal:")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)

        avatars = list_avatars()
        for i, avatar in enumerate(avatars):
            row = i // 3
            col = i % 3
            btn = QPushButton(avatar["name"])
            btn.setFixedSize(100, 80)
            btn.clicked.connect(lambda checked, aid=avatar["id"]: self._on_select(aid))
            grid.addWidget(btn, row, col)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _on_select(self, avatar_id: str):
        self.avatar_selected.emit(avatar_id)
        self.close()
