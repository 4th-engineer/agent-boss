"""Toolbar with action buttons."""
from PySide6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy
from PySide6.QtCore import Signal


class Toolbar(QToolBar):
    """Main toolbar with quick actions."""

    claude_clicked = Signal()
    hermes_clicked = Signal()
    new_tab_clicked = Signal()
    settings_clicked = Signal()
    theme_changed = Signal(str)
    avatar_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFixedHeight(40)
        self._colors = {
            "toolbar": "#252526",
            "button": "#3C3C3C",
            "fg": "#D4D4D4",
            "button_hover": "#505050"
        }
        self._apply_styles()
        self._setup_actions()

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QToolBar {{ background: {self._colors['toolbar']}; border: none; spacing: 4px; padding: 4px; }}
            QPushButton {{ background: {self._colors['button']}; color: {self._colors['fg']}; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; }}
            QPushButton:hover {{ background: {self._colors['button_hover']}; }}
        """)

    def update_colors(self, colors: dict):
        """Update toolbar colors from theme."""
        self._colors = {
            "toolbar": colors.get("toolbar", "#252526"),
            "button": colors.get("button", "#3C3C3C"),
            "fg": colors.get("fg", "#D4D4D4"),
            "button_hover": colors.get("button_hover", "#505050")
        }
        self._apply_styles()

    def _setup_actions(self):
        self._btn_claude = QPushButton("🤖 Claude")
        self._btn_claude.clicked.connect(lambda: self.claude_clicked.emit())
        self.addWidget(self._btn_claude)

        self._btn_hermes = QPushButton("🧙 Hermes")
        self._btn_hermes.clicked.connect(lambda: self.hermes_clicked.emit())
        self.addWidget(self._btn_hermes)

        self.addSeparator()

        self._btn_avatar = QPushButton("👾 Avatar")
        self._btn_avatar.clicked.connect(lambda: self.avatar_toggled.emit())
        self.addWidget(self._btn_avatar)

        self._btn_new = QPushButton("📁 New")
        self._btn_new.clicked.connect(lambda: self.new_tab_clicked.emit())
        self.addWidget(self._btn_new)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self._btn_settings = QPushButton("⚙️")
        self._btn_settings.clicked.connect(lambda: self.settings_clicked.emit())
        self.addWidget(self._btn_settings)
