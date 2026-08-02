"""Integration tests for parent online status API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _online_setup(db_session):
    parent = ParentAccount(wx_openid="test_online_p", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="online_test_fam")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="online_kid")
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
async def test_online_status_offline(async_client: AsyncClient, _online_setup):
    token, child_id = _online_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/online-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["online"] is False


@pytest.mark.asyncio
async def test_online_require_auth(async_client: AsyncClient):
    res = await async_client.get("/v1/api/parent/children/any-id/online-status")
    assert res.status_code == 401
