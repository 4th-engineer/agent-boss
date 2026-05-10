"""Room/World manager for agent grouping."""
import json
from pathlib import Path
from typing import Optional


class Room:
    """Represents a room/group for agents."""

    def __init__(self, id: str, name: str, description: str, color: str):
        self.id = id
        self.name = name
        self.description = description
        self.color = color
        self.members: list[str] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "members": self.members
        }

    @staticmethod
    def from_dict(data: dict) -> "Room":
        room = Room(
            data["id"], data["name"], data["description"], data["color"]
        )
        room.members = data.get("members", [])
        return room


class RoomManager:
    """Manages rooms and agent assignments."""

    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._agents: dict[str, str] = {}  # agent_id -> room_id
        self._load_rooms()

    def _get_rooms_path(self) -> Path:
        return Path(__file__).parent / "rooms.json"

    def _load_rooms(self):
        """Load rooms from JSON file."""
        path = self._get_rooms_path()
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                for room_data in data.values():
                    room = Room.from_dict(room_data)
                    self._rooms[room.id] = room
                    # Rebuild agent->room mapping
                    for member in room.members:
                        self._agents[member] = room.id

    def _save_rooms(self):
        """Save rooms to JSON file."""
        path = self._get_rooms_path()
        data = {rid: room.to_dict() for rid, room in self._rooms.items()}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def list_rooms(self) -> list[dict]:
        """Return list of all rooms."""
        return [room.to_dict() for room in self._rooms.values()]

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        return self._rooms.get(room_id)

    def create_room(self, name: str, description: str, color: str) -> Room:
        """Create a new room."""
        base_id = name.lower().replace(" ", "-")
        room_id = base_id
        counter = 1
        while room_id in self._rooms:
            room_id = f"{base_id}-{counter}"
            counter += 1
        room = Room(room_id, name, description, color)
        self._rooms[room_id] = room
        self._save_rooms()
        return room

    def delete_room(self, room_id: str) -> bool:
        """Delete a room. Agents move to main."""
        if room_id == "main":
            return False
        if room_id in self._rooms:
            # Ensure main room exists
            if "main" not in self._rooms:
                self._rooms["main"] = Room("main", "Main Hall", "Default room", "#007ACC")
            # Move agents to main (avoid duplicates)
            for agent_id in self._rooms[room_id].members:
                if agent_id not in self._rooms["main"].members:
                    self._rooms["main"].members.append(agent_id)
                    self._agents[agent_id] = "main"
            del self._rooms[room_id]
            self._save_rooms()
            return True
        return False

    def assign_agent(self, agent_id: str, room_id: str) -> bool:
        """Assign an agent to a room."""
        if room_id not in self._rooms:
            return False

        # Remove from current room
        current_room_id = self._agents.get(agent_id)
        if current_room_id and current_room_id in self._rooms:
            if agent_id in self._rooms[current_room_id].members:
                self._rooms[current_room_id].members.remove(agent_id)

        # Add to new room
        self._agents[agent_id] = room_id
        if agent_id not in self._rooms[room_id].members:
            self._rooms[room_id].members.append(agent_id)
        self._save_rooms()
        return True

    def get_agent_room(self, agent_id: str) -> Optional[str]:
        """Get room ID for an agent."""
        return self._agents.get(agent_id)

    def get_agents_in_room(self, room_id: str) -> list[str]:
        """Get all agent IDs in a room."""
        if room_id in self._rooms:
            return list(self._rooms[room_id].members)
        return []

    def unassigned_agents(self) -> list[str]:
        """Get agents in the main room but missing from the agent registry.

        Agents listed in main.members that have no _agents entry are considered
        unassigned — e.g., added to the JSON file but never registered via assign_agent().
        """
        main = self._rooms.get("main")
        if not main:
            return []
        registered = set(self._agents.keys())
        return [aid for aid in main.members if aid not in registered]
