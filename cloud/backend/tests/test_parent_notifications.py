"""Integration tests for parent notification API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _notif_setup(db_session):
    parent = ParentAccount(wx_openid="test_notif_p", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="notif_test_fam")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="notif_kid")
    db_session.add(child)
    await db_session.flush()
    pc = ParentChild(
        parent_id=parent.id, child_id=child.id,
        family_id=family.id, status="active", is_default=True,
    )
    db_session.add(pc)
    await db_session.commit()
    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id), str(parent.id)


@pytest.mark.asyncio
async def test_get_default_settings(async_client: AsyncClient, _notif_setup):
    token, child_id, _ = _notif_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/notification-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["settings"]["task_completed"] is True


@pytest.mark.asyncio
async def test_update_settings(async_client: AsyncClient, _notif_setup):
    token, child_id, _ = _notif_setup
    res = await async_client.put(
        f"/v1/api/parent/children/{child_id}/notification-settings",
        json={
            "settings": {"task_completed": False},
            "dnd": {"enabled": True, "start_time": "23:00", "end_time": "07:00"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["settings"]["task_completed"] is False
    assert body["data"]["dnd"]["enabled"] is True


@pytest.mark.asyncio
async def test_list_notifications_empty(async_client: AsyncClient, _notif_setup):
    token, _, _ = _notif_setup
    res = await async_client.get(
        "/v1/api/parent/notifications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_settings_require_auth(async_client: AsyncClient):
    res = await async_client.get(
        "/v1/api/parent/children/any-id/notification-settings",
    )
    assert res.status_code == 401
