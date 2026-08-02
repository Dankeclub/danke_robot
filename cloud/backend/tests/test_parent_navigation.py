"""Integration tests for parent navigation API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _nav_setup(db_session):
    parent = ParentAccount(wx_openid="test_nav_p", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="nav_test_fam")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="nav_kid")
    db_session.add(child)
    await db_session.flush()
    pc = ParentChild(
        parent_id=parent.id, child_id=child.id,
        family_id=family.id, status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()
    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.mark.asyncio
async def test_create_learning_navigation(async_client: AsyncClient, _nav_setup):
    token, child_id = _nav_setup
    res = await async_client.post(
        f"/v1/api/parent/children/{child_id}/navigations",
        json={
            "destination": "learning",
            "route_key": "learning_math",
            "module": "math",
            "title": "来做数学题",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["destination"] == "learning"
    assert body["data"]["navigation_id"] != ""


@pytest.mark.asyncio
async def test_create_chat_navigation(async_client: AsyncClient, _nav_setup):
    token, child_id = _nav_setup
    res = await async_client.post(
        f"/v1/api/parent/children/{child_id}/navigations",
        json={
            "destination": "chat",
            "route_key": "chat",
            "title": "和蛋仔聊天",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["destination"] == "chat"


@pytest.mark.asyncio
async def test_navigation_require_auth(async_client: AsyncClient):
    res = await async_client.post(
        "/v1/api/parent/children/any-id/navigations",
        json={"destination": "chat", "route_key": "chat"},
    )
    assert res.status_code == 401
