"""Pydantic schemas for car learning endpoints."""

from pydantic import BaseModel, Field


class ModuleConfigOut(BaseModel):
    """Module config exposed to the car."""
    module: str
    module_label: str
    enabled_for_today_task: bool
    difficulty: str | None = None
    difficulty_label: str | None = None
    category: str | None = None
    category_label: str | None = None
    batch_size: int
    min_repeat_interval_seconds: int
    config_version: int
    active_session_id: str | None = None


class LearningParkOut(BaseModel):
    """GET /learning/park response."""
    modules: list[ModuleConfigOut]


class SessionRequest(BaseModel):
    """POST /learning/{module}/sessions request body."""
    source: str = Field(..., description="today_task | free_learning | ws_navigation")
    task_id: str | None = None
    navigation_id: str | None = None


class ConfigSnapshotOut(BaseModel):
    """Frozen config at session/batch creation time."""
    difficulty: str | None = None
    difficulty_label: str | None = None
    category: str | None = None
    category_label: str | None = None
    batch_size: int
    min_repeat_interval_seconds: int
    config_version: int


class SessionOut(BaseModel):
    """POST /learning/{module}/sessions response."""
    session_id: str
    module: str
    source: str
    task_id: str | None = None
    status: str
    config_snapshot: ConfigSnapshotOut


_MODULE_LABELS = {
    "science": "科学探索",
    "math": "数学妙算",
    "english": "英语乐园",
    "poems": "诗词儿歌",
    "music": "音乐律动",
    "quiz": "益智问答",
}

_DIFFICULTY_LABELS: dict[str, dict[str, str]] = {
    "science": {"beginner": "初级", "intermediate": "中级", "advanced": "高级"},
    "math": {
        "within_10_add_subtract": "十以内加减法",
        "within_10_multiply_divide": "十以内乘除法",
        "two_digit_add_subtract": "两位数加减法",
        "two_digit_multiply_divide": "两位数乘除法",
        "three_digit_four_operations": "三位数加减乘除法",
        "mixed_four_operations": "四则混合运算",
    },
    "english": {"grade_3": "三年级", "grade_4": "四年级", "grade_5": "五年级", "grade_6": "六年级"},
    "poems": {
        "enlightenment": "启蒙", "beginner": "初级", "intermediate": "中级", "advanced": "高级"
    },
    "music": {},
    "quiz": {"beginner": "初级", "intermediate": "中级", "advanced": "高级"},
}

_CATEGORY_LABELS: dict[str, str] = {
    "children_song": "儿歌",
    "popular_music": "流行",
    "classical_music": "古典",
    "classic_music": "经典",
    "patriotic_music": "爱国",
    "mixed": "混合",
}


def module_label(module: str) -> str:
    return _MODULE_LABELS.get(module, module)


def difficulty_label(module: str, difficulty: str | None) -> str | None:
    if difficulty is None:
        return None
    return _DIFFICULTY_LABELS.get(module, {}).get(difficulty)


def category_label(category: str | None) -> str | None:
    if category is None:
        return None
    return _CATEGORY_LABELS.get(category)
