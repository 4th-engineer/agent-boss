"""Entry point for boss command."""
import sys
import argparse


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
        sys.exit(app.exec())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
