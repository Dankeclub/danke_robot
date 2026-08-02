"""Integration tests for parent usage API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _usage_setup(db_session):
    parent = ParentAccount(wx_openid="test_usage_p", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="usage_test_fam")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="usage_kid")
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
async def test_usage_series_empty(async_client: AsyncClient, _usage_setup):
    token, child_id = _usage_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/usage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]["series"]) > 0


@pytest.mark.asyncio
async def test_module_breakdown_empty(async_client: AsyncClient, _usage_setup):
    token, child_id = _usage_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/usage/modules",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_usage_require_auth(async_client: AsyncClient):
    res = await async_client.get("/v1/api/parent/children/any-id/usage")
    assert res.status_code == 401
