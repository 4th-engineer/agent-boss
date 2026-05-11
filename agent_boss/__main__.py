"""Entry point for boss command."""
import logging
import sys
import argparse

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog="boss", description="Agent Boss - Multi-tab terminal manager")
    parser.add_argument("command", nargs="?", default="run", help="Command to run (default: run)")
    args = parser.parse_args()

    if args.command == "run":
        from agent_boss.window import MainWindow
        from PySide6.QtWidgets import QApplication

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        exit_code = app.exec()
        logger.info("Agent Boss shutdown complete (exit_code=%d)", exit_code)
        sys.exit(exit_code)
    else:
        parser.print_help()


if __name__ == "__main__":
    # Top-level handler: catch any otherwise-uncaught exception from the Qt
    # event loop and log it before termination so it is not silently lost.
    try:
        main()
    except Exception:
        logger.critical("Uncaught exception during startup — aborting", exc_info=True)
        sys.exit(1)
