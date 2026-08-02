"""Parent usage schemas — daily/weekly/monthly usage and module breakdown."""

from datetime import date

from pydantic import BaseModel


class UsagePoint(BaseModel):
    date: date
    total_minutes: int


class UsageSeriesOut(BaseModel):
    granularity: str
    daily_goal_minutes: int = 30
    series: list[UsagePoint] = []


class ModuleUsage(BaseModel):
    module: str
    module_label: str
    minutes: int = 0
    percent: int = 0


class ModuleBreakdownOut(BaseModel):
    date: date
    total_minutes: int = 0
    modules: list[ModuleUsage] = []
