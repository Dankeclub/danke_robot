"""Parent reports routes — progress, sessions, wrong-answers, weekly."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_parent
from app.db import get_db
from app.parent.reports.schemas import (
    LearningProgressOut,
    LearningSessionOut,
    PaginatedSessions,
    PaginatedWrongAnswers,
    WeeklyReportListItem,
    WeeklyReportOut,
    WrongAnswerOut,
)
from app.parent.reports.service import (
    get_learning_progress,
    get_session_detail,
    get_sessions,
    get_weekly_report_detail,
    get_weekly_report_list,
    get_wrong_answers,
)
from app.schemas.common import error, ok

reports_router = APIRouter(prefix="/children", tags=["parent-reports"])


# --- Learning Progress ---

@reports_router.get("/{child_id}/learning/progress")
async def learning_progress(
    child_id: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get learning progress overview for a child."""
    try:
        data = await get_learning_progress(
            db, parent_id, child_id, start_date, end_date,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(LearningProgressOut(**data).model_dump())


# --- Learning Sessions ---

@reports_router.get("/{child_id}/learning/sessions")
async def list_sessions(
    child_id: str,
    module: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated learning sessions for a child."""
    try:
        data = await get_sessions(
            db, parent_id, child_id,
            module=module, status=status,
            start_date=start_date, end_date=end_date,
            page=page, page_size=page_size,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(PaginatedSessions(
        items=[LearningSessionOut(**item) for item in data["items"]],
        pagination=data["pagination"],
    ).model_dump())


@reports_router.get("/{child_id}/learning/sessions/{session_id}")
async def session_detail(
    child_id: str,
    session_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get a single learning session detail."""
    try:
        item = await get_session_detail(db, parent_id, child_id, session_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if item is None:
        return JSONResponse(status_code=404, content=error(404, "session_not_found"))

    return ok(LearningSessionOut(**item).model_dump())


# --- Wrong Answers ---

@reports_router.get("/{child_id}/learning/wrong-answers")
async def list_wrong_answers(
    child_id: str,
    module: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated wrong answers for a child."""
    try:
        data = await get_wrong_answers(
            db, parent_id, child_id,
            module=module, page=page, page_size=page_size,
        )
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok(PaginatedWrongAnswers(
        items=[WrongAnswerOut(**item) for item in data["items"]],
        pagination=data["pagination"],
    ).model_dump())


# --- Weekly Reports ---

@reports_router.get("/{child_id}/reports/weekly")
async def list_weekly_reports(
    child_id: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get list of recent weekly report keys."""
    try:
        items = await get_weekly_report_list(db, parent_id, child_id)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if items is None:
        return JSONResponse(status_code=404, content=error(404, "child_not_found"))

    return ok([WeeklyReportListItem(**item).model_dump() for item in items])


@reports_router.get("/{child_id}/reports/weekly/{week_key}")
async def weekly_report_detail(
    child_id: str,
    week_key: str,
    parent_id: str = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed weekly report for a specific week."""
    try:
        data = await get_weekly_report_detail(db, parent_id, child_id, week_key)
    except Exception:
        return JSONResponse(status_code=500, content=error(500, "internal_error"))

    if data is None:
        return JSONResponse(status_code=404, content=error(404, "report_not_found"))

    return ok(WeeklyReportOut(**data).model_dump())
