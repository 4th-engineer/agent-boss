"""Tab management for terminal sessions."""
from PySide6.QtWidgets import QTabWidget, QTabBar
from PySide6.QtCore import Signal, Qt
from .terminal import TerminalWidget
from .process_manager import ProcessManager
from .database import create_session, remove_session


class TabManager(QTabWidget):
    """Manages multiple terminal tabs."""

    tab_closed = Signal(str)  # tab_id

    def __init__(self, process_manager: ProcessManager, parent=None):
        super().__init__(parent)
        self._process_manager = process_manager
        self._tab_widgets = {}  # tab_id -> terminal widget

        self.setTabBar(TabBar())
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3C3C3C;
                background: #1E1E1E;
            }
            QTabBar::tab {
                background: #2D2D2D;
                color: #D4D4D4;
                padding: 6px 12px;
                border: 1px solid #3C3C3C;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #1E1E1E;
                border-bottom: 1px solid #1E1E1E;
            }
            QTabBar::tab:hover:!selected {
                background: #3C3C3C;
            }
            QTabBar::close-button {
                image: none;
            }
            QTabBar::close-button:hover {
                background: #C42B1C;
                border-radius: 2px;
            }
        """)

        self.tabCloseRequested.connect(self._on_tab_close)

    def create_tab(self, title: str = "PowerShell", working_dir: str = None) -> str:
        """Create a new terminal tab. Returns tab_id."""
        # Create PTY process
        process = self._process_manager.create_process(
            tab_id=title,  # Use title as temp id
            rows=24,
            cols=80,
        )
        if not process:
            return None

        # Create session in DB
        tab_id = create_session(title=title, working_dir=working_dir)

        # Update process key to actual tab_id
        self._process_manager.remove_process(title)
        self._process_manager._processes[tab_id] = process

        # Create terminal widget
        terminal = TerminalWidget(process, self)

        # Add tab
        index = self.addTab(terminal, title)
        self._tab_widgets[tab_id] = terminal

        # Select new tab
        self.setCurrentIndex(index)

        return tab_id

    def get_current_terminal(self):
        """Get current terminal widget."""
        index = self.currentIndex()
        if index >= 0:
            widget = self.widget(index)
            if isinstance(widget, TerminalWidget):
                return widget
        return None

    def get_current_tab_id(self) -> str:
        """Get tab_id for current tab."""
        for tab_id, widget in self._tab_widgets.items():
            if widget == self.widget(self.currentIndex()):
                return tab_id
        return None

    def _on_tab_close(self, index: int):
        """Handle tab close request."""
        widget = self.widget(index)
        if widget is None:
            return

        # Find and remove
        tab_id = None
        for tid, w in self._tab_widgets.items():
            if w == widget:
                tab_id = tid
                break

        if tab_id:
            self._process_manager.remove_process(tab_id)
            remove_session(tab_id)
            del self._tab_widgets[tab_id]

        self.removeTab(index)
        widget.cleanup()
        widget.deleteLater()

        if self.count() == 0:
            self.tab_closed.emit("all_closed")

    def close_all_tabs(self):
        """Close all tabs."""
        while self.count() > 0:
            self._on_tab_close(0)

    def run_command_in_current(self, command: str):
        """Send command to current terminal."""
        terminal = self.get_current_terminal()
        if terminal:
            terminal.write_input(command)


class TabBar(QTabBar):
    """Custom tab bar with + button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plus_button = None

    def tabSizeHint(self, index):
        return super().tabSizeHint(index)
