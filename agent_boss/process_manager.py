"""Cross-platform PTY process manager."""
import os
import sys
import fcntl
import termios
from typing import Optional


class PtyProcess:
    """Cross-platform PTY process wrapper."""

    def __init__(self, master_fd: int = None, pid: int = None, winpty_process=None):
        self._master_fd = master_fd
        self._pid = pid
        self._winpty_process = winpty_process
        self._closed = False

    @property
    def master_fd(self) -> Optional[int]:
        """Expose master_fd for PtyReader (read-only access)."""
        return self._master_fd

    @property
    def is_closed(self) -> bool:
        """Check if process has been closed."""
        return self._closed

    def write(self, data: str):
        if self._closed:
            return
        if self._winpty_process:
            try:
                self._winpty_process.write(data)
            except Exception as e:
                print(f"PtyProcess write error: {e}")
        elif self._master_fd is not None:
            try:
                os.write(self._master_fd, data.encode("utf-8"))
            except OSError as e:
                print(f"PtyProcess write error: {e}")

    def read(self) -> str:
        if self._closed:
            return ""
        if self._winpty_process:
            try:
                return self._winpty_process.read()
            except Exception as e:
                print(f"PtyProcess read error: {e}")
                return ""
        elif self._master_fd is not None:
            try:
                return os.read(self._master_fd, 65536).decode("utf-8", errors="replace")
            except OSError as e:
                print(f"PtyProcess read error: {e}")
                return ""
        return ""

    def resize(self, rows: int, cols: int):
        if self._winpty_process:
            try:
                self._winpty_process.set_size(cols, rows)
            except Exception as e:
                print(f"PtyProcess resize error: {e}")
        elif self._master_fd is not None:
            try:
                fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
            except OSError as e:
                print(f"PtyProcess resize error: {e}")

    def close(self):
        self._closed = True
        if self._winpty_process:
            try:
                self._winpty_process.kill()
            except Exception as e:
                print(f"PtyProcess close error (winpty): {e}")
            self._winpty_process = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError as e:
                print(f"PtyProcess close error (master_fd): {e}")
            self._master_fd = None
        if self._pid is not None:
            try:
                os.kill(self._pid, 9)
            except OSError as e:
                print(f"PtyProcess close error (kill pid): {e}")
            self._pid = None


class ProcessManager:
    """Manages PTY processes - cross-platform (Linux/macOS/Windows)."""

    def __init__(self):
        self._processes: dict[str, PtyProcess] = {}
        self._winpty = None

    def _init_winpty(self):
        if sys.platform == "win32" and self._winpty is None:
            try:
                import winpty
                self._winpty = winpty
            except ImportError:
                print("winpty not installed, Windows PTY not available")

    def create_process(self, tab_id: str, rows: int = 24, cols: int = 80):
        try:
            if sys.platform == "win32":
                return self._create_windows_process(tab_id, rows, cols)
            else:
                return self._create_unix_process(tab_id, rows, cols)
        except Exception as e:
            print(f"Failed to create PTY process: {e}")
            return None

    def _create_unix_process(self, tab_id: str, rows: int, cols: int):
        import pty
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()

        if pid == 0:
            # Child process
            try:
                os.close(master_fd)
                os.setsid()
                fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                os.close(slave_fd)
                shell = os.environ.get("SHELL", "/bin/bash")
                os.execvp(shell, [shell])
            except Exception:
                os._exit(1)
            os._exit(1)

        # Parent process
        try:
            os.close(slave_fd)
        except OSError:
            pass
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        process = PtyProcess(master_fd, pid)
        process.resize(rows, cols)
        self._processes[tab_id] = process
        return process

    def _create_windows_process(self, tab_id: str, rows: int, cols: int):
        self._init_winpty()
        if self._winpty is None:
            return None

        try:
            pt = self._winpty.PTY(cols, rows)
            pt.spawn("powershell.exe", ["-NoLogo", "-NoExit"], cwd=os.environ.get("USERPROFILE"))
            process = PtyProcess(winpty_process=pt)
            self._processes[tab_id] = process
            return process
        except Exception as e:
            print(f"Failed to create winpty process: {e}")
            return None

    def get_process(self, tab_id: str):
        return self._processes.get(tab_id)

    def remove_process(self, tab_id: str):
        if tab_id in self._processes:
            self._processes[tab_id].close()
            del self._processes[tab_id]

    def close_all(self):
        for proc in list(self._processes.values()):
            proc.close()
        self._processes.clear()
