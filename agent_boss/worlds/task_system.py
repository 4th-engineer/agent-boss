"""Task system for agent coordination."""
import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Task:
    """Represents a task assigned to an agent."""

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __init__(self, title: str, description: str, agent_id: str):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.agent_id = agent_id
        self.status = self.STATUS_PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent_id": self.agent_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TaskManager:
    """Manages tasks across all agents."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def create_task(self, title: str, description: str, agent_id: str) -> Task:
        """Create a new task."""
        task = Task(title, description, agent_id)
        self._tasks[task.id] = task
        logger.debug("Task created: %s for agent %s", task.id, agent_id)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_tasks_for_agent(self, agent_id: str) -> list[Task]:
        """Get all tasks for an agent."""
        return [t for t in self._tasks.values() if t.agent_id == agent_id]

    def update_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        if task_id in self._tasks:
            old_status = self._tasks[task_id].status
            self._tasks[task_id].status = status
            self._tasks[task_id].updated_at = datetime.now()
            logger.info("Task %s status: %s → %s", task_id, old_status, status)
            return True
        logger.warning("update_status: task %s not found", task_id)
        return False

    def list_tasks(self, status: Optional[str] = None) -> list[Task]:
        """List all tasks, optionally filtered by status."""
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())
