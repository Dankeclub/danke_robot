"""Parent dashboard schemas — aligned with parent-openapi.yaml."""

from datetime import date, datetime

from pydantic import BaseModel


class TaskProgress(BaseModel):
    """Progress info for a task."""
    completed_count: int = 0
    total_count: int = 0
    accuracy: float | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    is_final: bool | None = None


class TodayTask(BaseModel):
    """A single task in today's dashboard."""
    task_id: str
    task_category: str  # learning | lifestyle | sports | custom
    module: str | None = None
    module_label: str | None = None
    status: str  # assigned | claimed | in_progress | completed | expired
    title: str
    progress: TaskProgress
    expires_at: datetime | None = None


class ModuleProgress(BaseModel):
    """Per-module progress summary."""
    module: str
    module_label: str
    completed_tasks: int = 0
    total_tasks: int = 0
    accuracy: float | None = None
    active_sessions: int = 0


class DashboardTodayOut(BaseModel):
    """Today's dashboard data."""
    date: date
    total_tasks: int = 0
    completed_tasks: int = 0
    overall_accuracy: float | None = None
    total_correct: int = 0
    total_wrong: int = 0
    active_sessions: int = 0
    total_learning_minutes: int = 0
    tasks: list[TodayTask] = []
    modules: list[ModuleProgress] = []
