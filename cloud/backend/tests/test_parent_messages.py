"""Integration tests for parent messages API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _messages_setup(db_session):
    parent = ParentAccount(wx_openid="test_msgs_p", status="active")
    db_session.add(parent)
    await db_session.flush()
    family = Family(name="msgs_test_fam")
    db_session.add(family)
    await db_session.flush()
    child = Child(family_id=family.id, nickname="msgs_kid")
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
async def test_list_messages_empty(async_client: AsyncClient, _messages_setup):
    token, child_id = _messages_setup
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_send_text_message(async_client: AsyncClient, _messages_setup):
    token, child_id = _messages_setup
    res = await async_client.post(
        f"/v1/api/parent/children/{child_id}/messages",
        json={"type": "text", "content": {"text": "Hello"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["type"] == "text"
    assert body["data"]["content"]["text"] == "Hello"


@pytest.mark.asyncio
async def test_delete_message(async_client: AsyncClient, _messages_setup):
    token, child_id = _messages_setup
    # Create a message first
    create_res = await async_client.post(
        f"/v1/api/parent/children/{child_id}/messages",
        json={"type": "text", "content": {"text": "test"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    msg_id = create_res.json()["data"]["message_id"]
    # Delete it
    res = await async_client.delete(
        f"/v1/api/parent/children/{child_id}/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_messages_require_auth(async_client: AsyncClient):
    res = await async_client.get("/v1/api/parent/children/any-id/messages")
    assert res.status_code == 401
