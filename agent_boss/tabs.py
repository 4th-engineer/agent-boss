"""Tab management for terminal sessions."""
import logging
from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Signal
from agent_boss.terminal import TerminalWidget
from agent_boss.process_manager import ProcessManager
from agent_boss.database import create_session, remove_session

logger = logging.getLogger(__name__)


class TabManager(QTabWidget):
    """Manages multiple terminal tabs."""

    tab_closed = Signal(str)

    def __init__(self, process_manager: ProcessManager, parent=None):
        super().__init__(parent)
        self._process_manager = process_manager
        self._tab_widgets = {}

        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3C3C3C; background: #1E1E1E; }
            QTabBar::tab { background: #2D2D2D; color: #D4D4D4; padding: 6px 12px; border: 1px solid #3C3C3C; border-bottom: none; }
            QTabBar::tab:selected { background: #1E1E1E; }
            QTabBar::tab:hover:!selected { background: #3C3C3C; }
            QTabBar::close-button:hover { background: #C42B1C; border-radius: 2px; }
        """)
        self.tabCloseRequested.connect(self._on_tab_close)

    def create_tab(self, title="PowerShell", working_dir=None):
        # Use UUID-based tab_id from the start to avoid collisions
        tab_id = create_session(title=title, working_dir=working_dir)
        process = self._process_manager.create_process(tab_id=tab_id, rows=24, cols=80)
        if not process:
            remove_session(tab_id)
            return None

        terminal = TerminalWidget(process, self)
        index = self.addTab(terminal, title)
        self._tab_widgets[tab_id] = terminal
        self.setCurrentIndex(index)
        return tab_id

    def get_current_terminal(self):
        index = self.currentIndex()
        if index >= 0:
            widget = self.widget(index)
            if isinstance(widget, TerminalWidget):
                return widget
        return None

    def get_current_tab_id(self):
        widget = self.widget(self.currentIndex())
        for tid, w in self._tab_widgets.items():
            if w == widget:
                return tid
        return None

    def _on_tab_close(self, index):
        widget = self.widget(index)
        if widget is None:
            return

        tab_id = None
        for tid, w in self._tab_widgets.items():
            if w == widget:
                tab_id = tid
                break

        if tab_id:
            try:
                self._process_manager.remove_process(tab_id)
            except Exception as e:
                logger.warning("Failed to remove process for tab %s: %s — leaking process", tab_id, e)
            try:
                remove_session(tab_id)
            except Exception as e:
                logger.warning("Failed to remove session %s from DB: %s", tab_id, e)
            del self._tab_widgets[tab_id]

        self.removeTab(index)
        try:
            widget.cleanup()
        except Exception as e:
            logger.warning("Failed to cleanup widget for tab %s: %s", tab_id, e)
        widget.deleteLater()

        if self.count() == 0:
            self.tab_closed.emit("all_closed")

    def close_all_tabs(self):
        while self.count() > 0:
            self._on_tab_close(0)

    def run_command_in_current(self, command):
        terminal = self.get_current_terminal()
        if terminal:
            terminal.write_input(command)
