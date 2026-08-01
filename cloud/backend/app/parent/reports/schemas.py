"""Parent reports schemas — aligned with parent-openapi.yaml."""

from datetime import date, datetime

from pydantic import BaseModel

# --- Learning Progress ---

class ModuleProgressSummary(BaseModel):
    module: str
    module_label: str
    completed_tasks: int = 0
    total_tasks: int = 0
    accuracy: float | None = None
    total_correct: int = 0
    total_wrong: int = 0


class LearningProgressOut(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    modules: list[ModuleProgressSummary] = []
    overall_completed: int = 0
    overall_total: int = 0
    overall_accuracy: float | None = None
    overall_correct: int = 0
    overall_wrong: int = 0


# --- Session ---

class SessionSummary(BaseModel):
    completed_count: int = 0
    total_count: int = 0
    accuracy: float | None = None
    correct_count: int | None = None
    wrong_count: int | None = None
    total_active_duration_ms: int = 0


class LearningSessionOut(BaseModel):
    session_id: str
    module: str
    module_label: str
    source: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    summary: SessionSummary


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedSessions(BaseModel):
    items: list[LearningSessionOut]
    pagination: Pagination


# --- Wrong Answer ---

class Option(BaseModel):
    option_id: str
    text: str


class QuestionSnapshot(BaseModel):
    question_id: str
    question: str
    options: list[Option]
    correct_option_id: str


class WrongAnswerOut(BaseModel):
    wrong_answer_id: str
    module: str
    module_label: str
    question_snapshot: QuestionSnapshot | None = None
    selected_option_id: str
    first_wrong_at: datetime
    last_wrong_at: datetime
    wrong_count: int


class PaginatedWrongAnswers(BaseModel):
    items: list[WrongAnswerOut]
    pagination: Pagination


# --- Weekly Report ---

class WeeklyReportLearningSummary(BaseModel):
    total_active_duration_minutes: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0
    average_accuracy: float | None = None
    modules_touched: list[str] = []


class WeeklyReportSummary(BaseModel):
    focus_score: int = 0
    focus_change_percent: int = 0
    posture_score: int = 0
    posture_change_percent: int = 0
    anomaly_count: int = 0
    discovery_count: int = 0


class DailyScorePoint(BaseModel):
    date: date
    score: int


class WeeklyScorePoint(BaseModel):
    week_key: str
    score: int


class BehaviorInsightTag(BaseModel):
    text: str
    cls: str


class AnomalyItem(BaseModel):
    title: str
    description: str
    tags: list[BehaviorInsightTag] = []


class DiscoveryItem(BaseModel):
    title: str
    description: str
    color: str


class WeeklyReportOut(BaseModel):
    week_key: str
    label: str
    start_date: date
    end_date: date
    learning_summary: WeeklyReportLearningSummary
    behavior_summary: WeeklyReportSummary
    focus_daily_series: list[DailyScorePoint] = []
    posture_weekly_series: list[WeeklyScorePoint] = []
    anomalies: list[AnomalyItem] = []
    discoveries: list[DiscoveryItem] = []
    ai_summary: str = ""


class WeeklyReportListItem(BaseModel):
    week_key: str
    label: str
    start_date: date
    end_date: date
