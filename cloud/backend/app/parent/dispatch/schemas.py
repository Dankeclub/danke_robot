"""Parent dispatch schemas — aligned with parent-openapi.yaml."""

from datetime import datetime

from pydantic import BaseModel, Field

MODULE_LABELS = {
    "science": "科学探秘", "math": "数学思维",
    "english": "英语角", "poems": "诗词歌赋",
    "music": "音乐乐园", "quiz": "趣味问答",
}
VALID_TASK_CATEGORIES = {"learning", "lifestyle", "sports", "custom"}
VALID_MODULES = {"science", "math", "english", "poems", "music", "quiz"}


class TaskProgress(BaseModel):
    completed_count: int = 0
    total_count: int = 0
    accuracy: float | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    is_final: bool | None = None


class TodayTaskOut(BaseModel):
    task_id: str
    task_category: str
    module: str | None = None
    module_label: str | None = None
    status: str
    title: str
    progress: TaskProgress
    expires_at: datetime | None = None


class DispatchTaskItem(BaseModel):
    task_category: str = Field(..., pattern=r"^(learning|lifestyle|sports|custom)$")
    module: str | None = None
    title: str = Field(..., min_length=1)


class DispatchTasksRequest(BaseModel):
    tasks: list[DispatchTaskItem] = Field(..., min_length=1)
