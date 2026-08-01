"""Integration tests for parent learning goal API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _goal_setup(db_session):
    """Create parent and child, return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_goal", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="目标测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="目标孩子")
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
async def _goal_token(_goal_setup) -> str:
    return _goal_setup[0]


@pytest.fixture
async def _goal_child_id(_goal_setup) -> str:
    return _goal_setup[1]


@pytest.mark.asyncio
async def test_get_goal_default(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """GET goal returns defaults when not set."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["daily_goal_minutes"] == 30
    assert body["data"]["modules"] == []


@pytest.mark.asyncio
async def test_put_and_get_goal(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """PUT goal then GET returns the updated goal."""
    res = await async_client.put(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
        json={
            "daily_goal_minutes": 45,
            "modules": [
                {"module": "math", "goal_minutes": 20},
                {"module": "english", "goal_minutes": 15},
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["daily_goal_minutes"] == 45
    assert len(body["data"]["modules"]) == 2

    # Verify GET returns same data
    res2 = await async_client.get(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
    )
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["data"]["daily_goal_minutes"] == 45


@pytest.mark.asyncio
async def test_put_goal_invalid_module(
    async_client: AsyncClient, _goal_token: str, _goal_child_id: str,
):
    """PUT goal with invalid module returns 400."""
    res = await async_client.put(
        f"/v1/api/parent/children/{_goal_child_id}/learning/goal",
        headers={"Authorization": f"Bearer {_goal_token}"},
        json={
            "daily_goal_minutes": 30,
            "modules": [{"module": "invalid_mod", "goal_minutes": 10}],
        },
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_goal_requires_auth(async_client: AsyncClient):
    """Goal endpoint requires parent JWT."""
    res = await async_client.get(
        "/v1/api/parent/children/some-id/learning/goal",
    )
    assert res.status_code == 401
