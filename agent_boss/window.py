"""Main window for agent_boss."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from agent_boss.tabs import TabManager
from agent_boss.toolbar import Toolbar
from agent_boss.process_manager import ProcessManager
from agent_boss.database import init_db, get_all_sessions


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._process_manager = ProcessManager()
        init_db()
        self._setup_ui()
        self._restore_sessions()
        self._setup_shortcuts()

    def _setup_ui(self):
        self.setWindowTitle("Agent Boss")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow { background: #1E1E1E; }
            QStatusBar { background: #007ACC; color: #FFFFFF; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toolbar = Toolbar()
        self._toolbar.claude_clicked.connect(self._on_claude)
        self._toolbar.hermes_clicked.connect(self._on_hermes)
        self._toolbar.new_tab_clicked.connect(self._on_new_tab)
        self._toolbar.settings_clicked.connect(self._on_settings)
        layout.addWidget(self._toolbar)

        self._tab_manager = TabManager(self._process_manager)
        self._tab_manager.tab_closed.connect(self._on_all_tabs_closed)
        layout.addWidget(self._tab_manager)

        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready")
        self.setStatusBar(self._status_bar)

        if self._tab_manager.count() == 0:
            self._tab_manager.create_tab()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self._on_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self._close_current_tab)

    def _restore_sessions(self):
        sessions = get_all_sessions()
        for _ in sessions:
            self._tab_manager.create_tab()

    def _on_claude(self):
        self._tab_manager.run_command_in_current("claude --acp\n")
        self._status_bar.showMessage("Starting Claude...")

    def _on_hermes(self):
        self._tab_manager.run_command_in_current("hermes\n")
        self._status_bar.showMessage("Starting Hermes...")

    def _on_new_tab(self):
        title, ok = QInputDialog.getText(self, "New Terminal", "Tab name:", QLineEdit.Normal, "PowerShell")
        if ok and title:
            self._tab_manager.create_tab(title=title)
            self._status_bar.showMessage(f"Created: {title}")

    def _on_settings(self):
        QMessageBox.information(self, "Settings", "Settings coming soon...")

    def _close_current_tab(self):
        index = self._tab_manager.currentIndex()
        if index >= 0:
            self._tab_manager.tabCloseRequested.emit(index)

    def _on_all_tabs_closed(self):
        self._tab_manager.create_tab()

    def closeEvent(self, event):
        self._tab_manager.close_all_tabs()
        self._process_manager.close_all()
        event.accept()
