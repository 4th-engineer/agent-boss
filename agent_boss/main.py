"""Main entry point for Agent Boss."""
import logging
import sys
from PySide6.QtWidgets import QApplication
from .window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    # Qt event loop exited — log clean exit for observability
    logger.info("Agent Boss shutdown complete (exit_code=%d)", exit_code)
    sys.exit(exit_code)
