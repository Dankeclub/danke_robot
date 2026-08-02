"""Integration tests for car file upload API."""

import uuid

import pytest
from httpx import AsyncClient

from app.auth.security import hash_phone
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def car_files_setup(db_session):
    """Create test data: family, child, parent, parent-child binding."""
    family = Family(name="文件测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="文件测试孩子")
    db_session.add(child)
    await db_session.flush()

    phone = "+8613800138200"
    parent = ParentAccount(
        phone_e164=phone,
        phone_hash=hash_phone(phone),
        phone_masked="138****8200",
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
        "child_id": str(child.id),
        "family_id": str(family.id),
    }


async def _login(async_client: AsyncClient, phone: str) -> str:
    """Helper: login and return access_token."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": phone,
        "device_id": f"TEST-FILE-{uuid.uuid4().hex[:6]}",
        "device_name": "文件测试设备",
        "device_type": "car",
    })
    assert res.status_code == 200
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_init_upload(async_client: AsyncClient, car_files_setup):
    """POST /v1/api/car/files/uploads with valid data returns upload_id."""
    token = await _login(async_client, car_files_setup["phone"])

    res = await async_client.post(
        "/v1/api/car/files/uploads",
        json={
            "purpose": "poem_recording",
            "file_name": "poem.m4a",
            "content_type": "audio/mp4",
            "size_bytes": 182400,
            "sha256": "abc123hex",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["upload_id"] != ""


@pytest.mark.asyncio
async def test_complete_upload(async_client: AsyncClient, car_files_setup):
    """POST /v1/api/car/files/uploads/{id}/complete marks file available."""
    token = await _login(async_client, car_files_setup["phone"])

    # Init
    init_res = await async_client.post(
        "/v1/api/car/files/uploads",
        json={
            "purpose": "chat_asr",
            "file_name": "chat.m4a",
            "content_type": "audio/mp4",
            "size_bytes": 64000,
            "sha256": "def456hex",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    upload_id = init_res.json()["data"]["upload_id"]

    # Complete
    res = await async_client.post(
        f"/v1/api/car/files/uploads/{upload_id}/complete",
        json={"size_bytes": 64000, "sha256": "def456hex"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "available"


@pytest.mark.asyncio
async def test_car_files_require_auth(async_client: AsyncClient):
    """Car file endpoints require Bearer token."""
    res = await async_client.post(
        "/v1/api/car/files/uploads",
        json={
            "purpose": "poem_recording",
            "file_name": "x.m4a",
            "content_type": "audio/mp4",
            "size_bytes": 1,
            "sha256": "xx",
        },
    )
    assert res.status_code == 401
