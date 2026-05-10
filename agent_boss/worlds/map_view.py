"""Map view widget showing rooms and agents."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter


class RoomItem(QGraphicsRectItem):
    """Graphics item representing a room."""

    def __init__(self, room_id: str, name: str, color: str, member_count: int):
        super().__init__()
        self.room_id = room_id

        # Set appearance
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor(color).darker(150), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Room label
        self._label = QGraphicsTextItem(self)
        self._label.setPlainText(f"{name}\n{room_id}: {member_count}")
        self._label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self._label.setDefaultTextColor(QColor("#FFFFFF"))
        self._label.setPos(10, 10)
        self._label.setScale(1.5)

    def get_room_id(self) -> str:
        return self.room_id


class AgentNode(QGraphicsRectItem):
    """Graphics item representing an agent in a room."""

    def __init__(self, agent_id: str, avatar: str, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.avatar = avatar

        self.setBrush(QBrush(QColor("#607D8B")))
        self.setPen(QPen(QColor("#455A64"), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Agent label
        self._label = QGraphicsTextItem(self)
        self._label.setPlainText(agent_id[:8])
        self._label.setFont(QFont("Consolas", 8))
        self._label.setDefaultTextColor(QColor("#FFFFFF"))
        self._label.setScale(1.2)


class MapView(QGraphicsView):
    """Map view showing rooms and agents."""

    room_clicked = Signal(str)  # room_id
    agent_clicked = Signal(str)  # agent_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#1A1A2E")))
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self._room_items: dict[str, RoomItem] = {}
        self._agent_items: dict[str, AgentNode] = {}
        self._agent_rooms: dict[str, str] = {}  # agent_id -> room_id

    def clear_map(self):
        """Clear all items from the map."""
        self._scene.clear()
        self._room_items.clear()
        self._agent_items.clear()
        self._agent_rooms.clear()

    def add_room(self, room_id: str, name: str, color: str, x: float, y: float, member_count: int = 0):
        """Add a room to the map."""
        room = RoomItem(room_id, name, color, member_count)
        room.setRect(x, y, 150, 100)
        self._scene.addItem(room)
        self._room_items[room_id] = room

    def add_agent(self, agent_id: str, avatar: str, room_id: str):
        """Add an agent node to a room."""
        if room_id not in self._room_items:
            return

        room_item = self._room_items[room_id]
        room_rect = room_item.rect()

        # Position within room
        member_count = len([a for a in self._agent_rooms.values() if a == room_id])
        agent = AgentNode(agent_id, avatar)
        agent.setRect(room_rect.x() + 20 + (member_count % 3) * 40, room_rect.y() + 30 + (member_count // 3) * 40, 35, 35)
        self._scene.addItem(agent)
        self._agent_items[agent_id] = agent
        self._agent_rooms[agent_id] = room_id

    def move_agent_to_room(self, agent_id: str, room_id: str):
        """Move an agent to a different room."""
        if agent_id not in self._agent_items or room_id not in self._room_items:
            return

        self._agent_rooms[agent_id] = room_id
        # Visual update would require recalculating positions

    def mousePressEvent(self, event):
        """Handle click on items."""
        item = self.itemAt(event.pos())
        if isinstance(item, RoomItem):
            self.room_clicked.emit(item.get_room_id())
            event.accept()
        elif isinstance(item, AgentNode):
            self.agent_clicked.emit(item.agent_id)
            event.accept()
        super().mousePressEvent(event)


class MapWidget(QWidget):
    """Map widget with toolbar and view."""

    room_selected = Signal(str)
    agent_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._room_manager = None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        self._btn_refresh = QPushButton("🔄 Refresh")
        self._btn_add_room = QPushButton("➕ Room")
        toolbar.addWidget(self._btn_refresh)
        toolbar.addWidget(self._btn_add_room)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Map view
        self._map_view = MapView()
        layout.addWidget(self._map_view)

        # Connect signals
        self._map_view.room_clicked.connect(self.room_selected)
        self._map_view.agent_clicked.connect(self.agent_selected)

    def set_room_manager(self, room_manager):
        """Set the room manager and populate map."""
        self._room_manager = room_manager
        self.refresh_map()

    def refresh_map(self):
        """Refresh the map with current room/agent data."""
        if not self._room_manager:
            return

        self._map_view.clear_map()

        # Add rooms
        rooms = self._room_manager.list_rooms()
        positions = [(50, 50), (220, 50), (50, 180), (220, 180)]
        for i, room in enumerate(rooms):
            x, y = positions[i] if i < len(positions) else (50 + i * 170, 50)
            self._map_view.add_room(
                room["id"], room["name"], room["color"], x, y,
                len(room.get("members", []))
            )

    def get_map_view(self) -> MapView:
        return self._map_view
