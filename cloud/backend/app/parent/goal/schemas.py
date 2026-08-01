"""Parent learning goal schemas — aligned with parent-openapi.yaml."""

from pydantic import BaseModel, Field

VALID_MODULES = {"science", "math", "english", "poems", "music", "quiz"}
MODULE_LABELS = {
    "science": "科学探秘",
    "math": "数学思维",
    "english": "英语角",
    "poems": "诗词歌赋",
    "music": "音乐乐园",
    "quiz": "趣味问答",
}


class LearningGoalModule(BaseModel):
    """Per-module goal minutes."""
    module: str
    module_label: str = ""
    goal_minutes: int = 0


class LearningGoalOut(BaseModel):
    """GET / PUT response for learning goal."""
    daily_goal_minutes: int = 30
    modules: list[LearningGoalModule] = []


class UpdateLearningGoalRequest(BaseModel):
    """PUT request body for updating learning goal."""
    daily_goal_minutes: int = Field(..., ge=0)
    modules: list[LearningGoalModule] = Field(default_factory=list)
