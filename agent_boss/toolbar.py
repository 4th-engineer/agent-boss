"""Toolbar with action buttons."""
from PySide6.QtWidgets import QToolBar, QPushButton, QWidget, QSizePolicy
from PySide6.QtCore import Signal


class Toolbar(QToolBar):
    """Main toolbar with quick actions."""

    claude_clicked = Signal()
    hermes_clicked = Signal()
    new_tab_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QToolBar { background: #252526; border: none; spacing: 4px; padding: 4px; }
            QPushButton { background: #3C3C3C; color: #D4D4D4; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; }
            QPushButton:hover { background: #505050; }
        """)
        self._setup_actions()

    def _setup_actions(self):
        self._btn_claude = QPushButton("🤖 Claude")
        self._btn_claude.clicked.connect(self.claude_clicked.emit)
        self.addWidget(self._btn_claude)

        self._btn_hermes = QPushButton("🧙 Hermes")
        self._btn_hermes.clicked.connect(self.hermes_clicked.emit)
        self.addWidget(self._btn_hermes)

        self.addSeparator()

        self._btn_new = QPushButton("📁 New")
        self._btn_new.clicked.connect(self.new_tab_clicked.emit)
        self.addWidget(self._btn_new)

        self._btn_settings = QPushButton("⚙️")
        self._btn_settings.clicked.connect(self.settings_clicked.emit)
        self.addWidget(self._btn_settings)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
