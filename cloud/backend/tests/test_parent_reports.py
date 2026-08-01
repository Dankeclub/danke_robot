"""Integration tests for parent reports API — progress, sessions, wrong-answers, weekly."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.learning import LearningSession
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.models.task import DailyTask


@pytest.fixture
async def _reports_setup(db_session):
    """Create parent, child. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_reports", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="报告测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="报告孩子")
    db_session.add(child)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, child_id=child.id, family_id=family.id,
        status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()

    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.fixture
async def _reports_token(_reports_setup) -> str:
    return _reports_setup[0]


@pytest.fixture
async def _reports_child_id(_reports_setup) -> str:
    return _reports_setup[1]


@pytest.mark.asyncio
async def test_progress_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET progress returns empty when no data."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/progress",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["modules"] == []
    assert body["data"]["overall_total"] == 0


@pytest.mark.asyncio
async def test_progress_with_data(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET progress returns aggregated stats when data exists."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_reports_child_id, business_date=today,
        module="math", task_category="learning",
        title="今日数学", status="completed",
        progress_completed=10, progress_total=10, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/progress",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["overall_total"] >= 1


@pytest.mark.asyncio
async def test_sessions_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET sessions returns empty pagination when no data."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []
    assert body["data"]["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_sessions_with_data(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET sessions returns session list when data exists."""
    session = LearningSession(
        child_id=_reports_child_id, module="math",
        source="today_task", status="active",
    )
    db_session.add(session)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]["items"]) >= 1
    assert body["data"]["items"][0]["module"] == "math"


@pytest.mark.asyncio
async def test_session_detail(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str, db_session,
):
    """GET sessions/{id} returns session detail."""
    session = LearningSession(
        child_id=_reports_child_id, module="science",
        source="free_learning", status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/sessions/{session.id}",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["module"] == "science"
    assert body["data"]["source"] == "free_learning"


@pytest.mark.asyncio
async def test_wrong_answers_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET wrong-answers returns empty pagination."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/learning/wrong-answers",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_weekly_list(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET weekly returns week key list."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/reports/weekly",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 8  # 8 weeks


@pytest.mark.asyncio
async def test_weekly_detail_empty(
    async_client: AsyncClient, _reports_token: str, _reports_child_id: str,
):
    """GET weekly/{week_key} returns report with empty data."""
    # Use a recent Monday as week_key
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_key = monday.isoformat()

    res = await async_client.get(
        f"/v1/api/parent/children/{_reports_child_id}/reports/weekly/{week_key}",
        headers={"Authorization": f"Bearer {_reports_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["week_key"] == week_key
    assert body["data"]["learning_summary"]["completed_tasks"] == 0
    assert body["data"]["ai_summary"] == ""


@pytest.mark.asyncio
async def test_reports_require_auth(async_client: AsyncClient):
    """Reports endpoints require parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/learning/progress",
    )
    assert res.status_code == 401
