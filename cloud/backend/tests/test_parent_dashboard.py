"""Integration tests for parent dashboard API."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild
from app.models.task import DailyTask


@pytest.fixture
async def _dash_setup(db_session):
    """Create parent, child. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_dash", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="大盘测试")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="大盘孩子")
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
async def _dash_token(_dash_setup) -> str:
    return _dash_setup[0]


@pytest.fixture
async def _dash_child_id(_dash_setup) -> str:
    return _dash_setup[1]


@pytest.mark.asyncio
async def test_dashboard_today_empty(
    async_client: AsyncClient, _dash_token: str, _dash_child_id: str,
):
    """GET dashboard/today returns empty data when no tasks exist."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_dash_child_id}/dashboard/today",
        headers={"Authorization": f"Bearer {_dash_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["total_tasks"] == 0
    assert body["data"]["completed_tasks"] == 0
    assert body["data"]["tasks"] == []


@pytest.mark.asyncio
async def test_dashboard_today_with_tasks(
    async_client: AsyncClient, _dash_token: str, _dash_child_id: str, db_session,
):
    """GET dashboard/today returns tasks when they exist."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_dash_child_id,
        business_date=today,
        module="science",
        task_category="learning",
        title="今日科学任务",
        status="assigned",
        progress_completed=0,
        progress_total=10,
        expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_dash_child_id}/dashboard/today",
        headers={"Authorization": f"Bearer {_dash_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["total_tasks"] == 1
    assert len(body["data"]["tasks"]) == 1
    assert body["data"]["tasks"][0]["title"] == "今日科学任务"
    assert body["data"]["tasks"][0]["module"] == "science"


@pytest.mark.asyncio
async def test_dashboard_requires_parent_auth(async_client: AsyncClient):
    """Dashboard endpoint requires parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/dashboard/today",
    )
    assert res.status_code == 401
