"""Integration tests for parent dispatch API — today-tasks + dispatched."""

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
async def _dispatch_setup(db_session):
    """Create parent, child. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_dispatch", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="派发测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="派发孩子")
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
async def _dispatch_token(_dispatch_setup) -> str:
    return _dispatch_setup[0]


@pytest.fixture
async def _dispatch_child_id(_dispatch_setup) -> str:
    return _dispatch_setup[1]


@pytest.mark.asyncio
async def test_today_tasks_empty(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """GET today-tasks returns empty when no tasks exist."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_today_tasks_with_data(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str, db_session,
):
    """GET today-tasks returns learning tasks."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_dispatch_child_id, business_date=today,
        module="math", task_category="learning",
        title="今日数学思维", status="assigned",
        progress_total=10, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["module"] == "math"


@pytest.mark.asyncio
async def test_today_task_detail(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str, db_session,
):
    """GET today-tasks/{id} returns task detail."""
    tz = timezone(timedelta(hours=8))
    today = datetime.now(tz).date()
    expires = datetime.now(tz) + timedelta(hours=23)

    task = DailyTask(
        child_id=_dispatch_child_id, business_date=today,
        module="science", task_category="learning",
        title="今日科学探秘", status="assigned",
        progress_total=5, expires_at=expires,
    )
    db_session.add(task)
    await db_session.commit()

    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks/{task.id}",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["title"] == "今日科学探秘"


@pytest.mark.asyncio
async def test_dispatched_tasks_crud(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """POST and GET dispatched-tasks."""
    # Create dispatched tasks
    res = await async_client.post(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
        json={
            "tasks": [
                {"task_category": "lifestyle", "title": "刷牙"},
                {"task_category": "sports", "title": "跳绳100下"},
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 2

    # Get dispatched tasks
    res2 = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert len(body2["data"]) == 2


@pytest.mark.asyncio
async def test_dispatched_tasks_excluded_from_today(
    async_client: AsyncClient, _dispatch_token: str, _dispatch_child_id: str,
):
    """Dispatched tasks are NOT returned in today-tasks."""
    # Create dispatched task
    await async_client.post(
        f"/v1/api/parent/children/{_dispatch_child_id}/dispatched-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
        json={"tasks": [{"task_category": "lifestyle", "title": "整理书包"}]},
    )

    # today-tasks should not include it
    res = await async_client.get(
        f"/v1/api/parent/children/{_dispatch_child_id}/today-tasks",
        headers={"Authorization": f"Bearer {_dispatch_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 0  # no learning tasks created


@pytest.mark.asyncio
async def test_dispatch_requires_auth(async_client: AsyncClient):
    """Dispatch endpoints require parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/dispatched-tasks",
    )
    assert res.status_code == 401
