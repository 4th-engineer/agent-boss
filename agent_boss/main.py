"""Main entry point for Agent Boss."""
import logging
import sys
from PySide6.QtWidgets import QApplication
from .window import MainWindow

# Configure logging once at application start — all modules inherit this setup.
# Default: WARNING+ to stderr (visible in dev); set AGENTBOSS_LOG=info/debug to enable.
_log_level = getattr(logging, (sys.environ.get("AGENTBOSS_LOG") or "warning").upper(), "WARNING")
_log_fmt = "%(name)s [%(levelname)s] %(message)s"
logging.basicConfig(level=_log_level, format=_log_fmt, stream=sys.stderr)

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
