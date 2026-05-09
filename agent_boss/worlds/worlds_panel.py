"""Worlds panel - combines map view and agent detail."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTabWidget, QListWidget
)
from PySide6.QtCore import Qt

from agent_boss.worlds.map_view import MapWidget
from agent_boss.worlds.agent_detail import AgentDetailPanel
from agent_boss.worlds.room_manager import RoomManager
from agent_boss.worlds.task_system import TaskManager


class WorldsPanel(QWidget):
    """Main panel for Phase 4 interaction system."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._room_manager = RoomManager()
        self._task_manager = TaskManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Left: Room list + Map
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Room tabs
        self._room_tabs = QTabWidget()
        self._room_list = QListWidget()
        self._room_tabs.addTab(self._room_list, "Rooms")
        left_layout.addWidget(self._room_tabs)

        # Map view
        self._map_widget = MapWidget()
        self._map_widget.set_room_manager(self._room_manager)
        self._map_widget.room_selected.connect(self._on_room_selected)
        self._map_widget.agent_selected.connect(self._on_agent_selected)
        left_layout.addWidget(self._map_widget)

        # Right: Agent detail panel
        self._detail_panel = AgentDetailPanel()
        self._detail_panel.command_sent.connect(self._on_command_sent)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self._detail_panel)
        splitter.setSizes([600, 300])
        layout.addWidget(splitter)

        # Populate room list
        self._refresh_rooms()

    def _refresh_rooms(self):
        """Refresh the room list."""
        self._room_list.clear()
        for room in self._room_manager.list_rooms():
            members = room.get("members", [])
            self._room_list.addItem(f'{room["name"]} ({len(members)})')

    def _on_room_selected(self, room_id: str):
        """Handle room click."""
        room = self._room_manager.get_room(room_id)
        if room:
            agents = room.members
            if agents:
                self._detail_panel.set_agent(agents[0], room=room_id)

    def _on_agent_selected(self, agent_id: str):
        """Handle agent click."""
        room_id = self._room_manager.get_agent_room(agent_id)
        avatar = "beaver"  # Default
        self._detail_panel.set_agent(agent_id, avatar, room_id or "main")

    def _on_command_sent(self, agent_id: str, cmd: str):
        """Handle command sent to agent."""
        print(f"Command to {agent_id}: {cmd}")

    def get_task_manager(self) -> TaskManager:
        """Get the task manager."""
        return self._task_manager

    def get_room_manager(self) -> RoomManager:
        """Get the room manager."""
        return self._room_manager
