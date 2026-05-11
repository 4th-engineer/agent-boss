"""Agent detail panel for viewing agent info and sending commands."""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget
)
from PySide6.QtCore import Signal

logger = logging.getLogger(__name__)


class AgentDetailPanel(QWidget):
    """Panel showing agent details and command input."""

    command_sent = Signal(str, str)  # agent_id, command

    def __init__(self, parent=None):
        super().__init__(parent)
        self._agent_id = None
        self._agent_avatar = "beaver"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        self._avatar_label = QLabel("Avatar")
        self._avatar_label.setStyleSheet("font-size: 32px;")
        header.addWidget(self._avatar_label)

        info = QVBoxLayout()
        self._name_label = QLabel("Agent: -")
        self._name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        info.addWidget(self._name_label)
        self._status_label = QLabel("Status: Idle")
        info.addWidget(self._status_label)
        self._room_label = QLabel("Room: main")
        info.addWidget(self._room_label)
        header.addLayout(info)
        header.addStretch()
        layout.addLayout(header)

        # Task history
        history_label = QLabel("Task History:")
        layout.addWidget(history_label)
        self._history_list = QListWidget()
        self._history_list.addItem("No tasks yet")
        layout.addWidget(self._history_list)

        # Command input
        cmd_label = QLabel("Send Command:")
        layout.addWidget(cmd_label)
        cmd_layout = QHBoxLayout()
        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("Type a command...")
        self._cmd_input.returnPressed.connect(self._send_command)
        cmd_layout.addWidget(self._cmd_input)
        self._send_btn = QPushButton("Send")
        self._send_btn.clicked.connect(self._send_command)
        cmd_layout.addWidget(self._send_btn)
        layout.addLayout(cmd_layout)

        # Quick commands
        quick_label = QLabel("Quick Commands:")
        layout.addWidget(quick_label)
        quick_layout = QHBoxLayout()
        self._btn_status = QPushButton("Status")
        self._btn_status.clicked.connect(lambda: self._quick_cmd("status"))
        quick_layout.addWidget(self._btn_status)
        self._btn_tasks = QPushButton("Tasks")
        self._btn_tasks.clicked.connect(lambda: self._quick_cmd("tasks"))
        quick_layout.addWidget(self._btn_tasks)
        self._btn_ping = QPushButton("Ping")
        self._btn_ping.clicked.connect(lambda: self._quick_cmd("ping"))
        quick_layout.addWidget(self._btn_ping)
        layout.addLayout(quick_layout)

        layout.addStretch()

    def set_agent(self, agent_id: str, avatar: str = "beaver", room: str = "main"):
        """Set the agent to display."""
        self._agent_id = agent_id
        self._agent_avatar = avatar
        self._name_label.setText(f"Agent: {agent_id[:12]}")
        self._room_label.setText(f"Room: {room}")
        self._status_label.setText("Status: Active")

    def _send_command(self):
        """Send command to agent."""
        cmd = self._cmd_input.text().strip()
        if cmd and self._agent_id:
            self.command_sent.emit(self._agent_id, cmd)
            self._history_list.addItem(f"> {cmd}")
            self._history_list.scrollToBottom()
            self._cmd_input.clear()

    def _quick_cmd(self, cmd: str):
        """Send a quick command."""
        if self._agent_id:
            self._cmd_input.setText(cmd)
            self._send_command()
