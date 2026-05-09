"""Main window for agentstudio."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent

from .tabs import TabManager
from .toolbar import Toolbar
from .process_manager import ProcessManager
from .database import init_db, get_all_sessions


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._process_manager = ProcessManager()

        # Initialize database
        init_db()

        self._setup_ui()
        self._restore_sessions()
        self._setup_shortcuts()

    def _setup_ui(self):
        self.setWindowTitle("Agent Boss")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow {
                background: #1E1E1E;
            }
            QStatusBar {
                background: #007ACC;
                color: #FFFFFF;
            }
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self._toolbar = Toolbar()
        self._toolbar.claude_clicked.connect(self._on_claude)
        self._toolbar.hermes_clicked.connect(self._on_hermes)
        self._toolbar.new_tab_clicked.connect(self._on_new_tab)
        self._toolbar.settings_clicked.connect(self._on_settings)
        layout.addWidget(self._toolbar)

        # Tab manager
        self._tab_manager = TabManager(self._process_manager)
        self._tab_manager.tab_closed.connect(self._on_all_tabs_closed)
        layout.addWidget(self._tab_manager)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.showMessage("就绪")
        self.setStatusBar(self._status_bar)

        # Create initial tab if none exist
        if self._tab_manager.count() == 0:
            self._tab_manager.create_tab()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Ctrl+T: New tab
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self._on_new_tab)
        # Ctrl+W: Close tab
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self._close_current_tab)
        # Ctrl+Tab: Next tab
        QShortcut(QKeySequence("Ctrl+Tab"), self, activated=self._tab_manager.raise_)
        # Ctrl+Shift+Tab: Previous tab
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, activated=self._tab_manager.raise_)

    def _restore_sessions(self):
        """Restore previous sessions from database."""
        sessions = get_all_sessions()
        # For now, just restore tab count (create blank tabs)
        for _ in sessions:
            self._tab_manager.create_tab()

    def _on_claude(self):
        """Run claude --acp in current terminal."""
        self._tab_manager.run_command_in_current("claude --acp\n")
        self._status_bar.showMessage("启动 Claude...")

    def _on_hermes(self):
        """Run hermes in current terminal."""
        self._tab_manager.run_command_in_current("hermes\n")
        self._status_bar.showMessage("启动 Hermes...")

    def _on_new_tab(self):
        """Create new terminal tab."""
        title, ok = QInputDialog.getText(self, "新建终端", "标签名称:", QLineEdit.Normal, "PowerShell")
        if ok and title:
            self._tab_manager.create_tab(title=title)
            self._status_bar.showMessage(f"已创建标签: {title}")

    def _on_settings(self):
        """Open settings dialog."""
        QMessageBox.information(self, "设置", "设置功能开发中...")

    def _close_current_tab(self):
        """Close current tab."""
        index = self._tab_manager.currentIndex()
        if index >= 0:
            self._tab_manager.tabCloseRequested.emit(index)

    def _on_all_tabs_closed(self):
        """Handle all tabs closed."""
        # Optionally quit or create new tab
        self._tab_manager.create_tab()

    def closeEvent(self, event):
        """Cleanup on close."""
        self._tab_manager.close_all_tabs()
        self._process_manager.close_all()
        event.accept()
