import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.auth.security import hash_phone
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild

BATCH_URL = "/v1/api/car/telemetry/events:batch"


@pytest.fixture
async def telemetry_setup(db_session):
    """Create test data with an active device binding."""
    family = Family(name="遥测家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="遥测孩子")
    db_session.add(child)
    await db_session.flush()

    phone = "+8613800138001"
    parent = ParentAccount(
        phone_e164=phone,
        phone_hash=hash_phone(phone),
        phone_masked="138****8001",
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
    await db_session.commit()

    return {
        "phone": phone,
        "family_id": str(family.id),
        "child_id": str(child.id),
    }


@pytest.mark.asyncio
async def test_batch_events(async_client: AsyncClient, telemetry_setup):
    """POST /v1/api/car/telemetry/events:batch accepts events."""
    # Login first
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": telemetry_setup["phone"],
        "device_id": "TELEM-DEV-001",
        "device_name": "遥测设备",
        "device_type": "car",
    })
    token = login_res.json()["data"]["access_token"]

    event_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    res = await async_client.post(
        BATCH_URL,
        json={
            "events": [
                {
                    "event_id": event_id,
                    "event_type": "learning.session.start",
                    "module": "math",
                    "timestamp": now,
                    "payload": {"session_id": "sess-001"},
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["accepted"] == 1
    assert body["data"]["duplicates"] == 0


@pytest.mark.asyncio
async def test_batch_events_idempotent(async_client: AsyncClient, telemetry_setup):
    """Repeating the same event_id returns accepted=0, duplicates=1."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": telemetry_setup["phone"],
        "device_id": "TELEM-DEV-002",
        "device_name": "幂等设备",
        "device_type": "car",
    })
    token = login_res.json()["data"]["access_token"]

    event_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    event_payload = {
        "events": [
            {
                "event_id": event_id,
                "event_type": "learning.session.start",
                "module": "math",
                "timestamp": now,
                "payload": {},
            }
        ]
    }
    headers = {"Authorization": f"Bearer {token}"}

    # First request
    res1 = await async_client.post(BATCH_URL, json=event_payload, headers=headers)
    assert res1.json()["data"]["accepted"] == 1

    # Second request — same event_id
    res2 = await async_client.post(BATCH_URL, json=event_payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["data"]["accepted"] == 0
    assert res2.json()["data"]["duplicates"] == 1


@pytest.mark.asyncio
async def test_batch_events_unauthorized(async_client: AsyncClient):
    """POST without auth token returns 401."""
    res = await async_client.post(
        BATCH_URL,
        json={
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "test",
                    "timestamp": "2026-07-26T10:00:00+08:00",
                }
            ]
        },
    )
    assert res.status_code == 401
