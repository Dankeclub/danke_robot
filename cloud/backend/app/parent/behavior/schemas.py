"""Parent behavior schemas — focus, posture, location, insights."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class BehaviorScorePoint(BaseModel):
    date: date
    score: int


class BehaviorStat(BaseModel):
    label: str
    value: float
    unit: str


class FocusOut(BaseModel):
    period: str
    score: int = 0
    change_percent: int = 0
    stats: list[BehaviorStat] = Field(default_factory=list)
    daily_series: list[BehaviorScorePoint] = Field(default_factory=list)


class PostureDistribution(BaseModel):
    label: str
    percent: int


class PostureOut(BaseModel):
    period: str
    score: int = 0
    change_percent: int = 0
    reminder_count: int = 0
    distribution: list[PostureDistribution] = Field(default_factory=list)
    weekly_series: list[BehaviorScorePoint] = Field(default_factory=list)


class ZoneDistribution(BaseModel):
    zone: str
    percent: int


class LocationOut(BaseModel):
    period: str
    active_zones_count: int = 0
    distribution: list[ZoneDistribution] = Field(default_factory=list)
    anomaly_detected: bool = False


class InsightTag(BaseModel):
    text: str
    cls: str


class InsightItem(BaseModel):
    insight_id: str
    type: str
    title: str
    description: str
    tags: list[InsightTag] = Field(default_factory=list)
    occurred_at: datetime | None = None


class InsightsOut(BaseModel):
    items: list[InsightItem] = Field(default_factory=list)
