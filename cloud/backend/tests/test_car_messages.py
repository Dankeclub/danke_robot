"""Integration tests for car parent messages API."""

import uuid

import pytest
from httpx import AsyncClient

from app.auth.security import hash_phone
from app.models.child import Child
from app.models.family import Family
from app.models.message import ParentMessage
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def car_messages_setup(db_session):
    """Create test data: family, child, parent, binding, and a parent message."""
    family = Family(name="消息测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="消息测试孩子")
    db_session.add(child)
    await db_session.flush()

    phone = "+8613800138300"
    parent = ParentAccount(
        phone_e164=phone,
        phone_hash=hash_phone(phone),
        phone_masked="138****8300",
        status="active",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
        is_default=True,
    )
    db_session.add(pc)

    # Seed a parent→child text message so list is not empty
    msg = ParentMessage(
        child_id=child.id,
        parent_id=parent.id,
        direction="parent_to_child",
        msg_type="text",
        content={"text": "记得完成今天的数学任务哦。"},
    )
    db_session.add(msg)
    await db_session.commit()

    return {
        "phone": phone,
        "child_id": str(child.id),
        "family_id": str(family.id),
        "parent_id": str(parent.id),
        "message_id": str(msg.id),
    }


async def _login(async_client: AsyncClient, phone: str) -> str:
    """Helper: login and return access_token."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": phone,
        "device_id": f"TEST-MSG-{uuid.uuid4().hex[:6]}",
        "device_name": "消息测试设备",
        "device_type": "car",
    })
    assert res.status_code == 200
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_list_messages(async_client: AsyncClient, car_messages_setup):
    """GET /v1/api/car/parent-messages returns recent messages."""
    token = await _login(async_client, car_messages_setup["phone"])

    res = await async_client.get(
        "/v1/api/car/parent-messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) >= 1
    assert items[0]["type"] == "text"
    assert items[0]["message_id"] != ""


@pytest.mark.asyncio
async def test_send_preset_text_reply(async_client: AsyncClient, car_messages_setup):
    """POST /v1/api/car/parent-messages/{id}/replies with preset_text."""
    token = await _login(async_client, car_messages_setup["phone"])

    res = await async_client.post(
        f"/v1/api/car/parent-messages/{car_messages_setup['message_id']}/replies",
        json={"type": "preset_text", "preset_code": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["type"] == "preset_text"
    assert body["data"]["preset_code"] == "got_it"
    assert body["data"]["text"] == "知道了"


@pytest.mark.asyncio
async def test_car_messages_require_auth(async_client: AsyncClient):
    """Car parent-messages endpoints require Bearer token."""
    res = await async_client.get("/v1/api/car/parent-messages")
    assert res.status_code == 401
