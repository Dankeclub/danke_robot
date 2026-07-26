"""Integration tests for car auth API endpoints."""

import pytest
from httpx import AsyncClient

from app.auth.security import hash_phone
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def car_login_setup(db_session):
    """Create test data: family, child, parent, parent-child binding."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小测试")
    db_session.add(child)
    await db_session.flush()

    phone = "+8613800138000"
    parent = ParentAccount(
        phone_e164=phone,
        phone_hash=hash_phone(phone),
        phone_masked="138****8000",
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
        "phone_hash": hash_phone(phone),
        "family_id": str(family.id),
        "child_id": str(child.id),
        "parent_id": str(parent.id),
    }


@pytest.mark.asyncio
async def test_car_login_success(async_client: AsyncClient, car_login_setup, db_session):
    """POST /v1/api/car/auth/login with valid phone returns token pair and child profile."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-001",
        "device_name": "测试设备",
        "device_type": "car",
    })

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None
    assert body["data"]["expires_in"] == 7200
    assert body["data"]["child_profile"]["nickname"] == "小测试"


@pytest.mark.asyncio
async def test_car_login_phone_not_bound(async_client: AsyncClient):
    """POST /v1/api/car/auth/login with unknown phone returns 404."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": "+8613900000000",
        "device_id": "TEST-DEV-002",
        "device_name": "未知设备",
        "device_type": "car",
    })

    assert res.status_code == 404
    body = res.json()
    assert body["msg"] == "phone_not_bound"


@pytest.mark.asyncio
async def test_car_refresh_token(async_client: AsyncClient, car_login_setup):
    """POST /v1/api/car/auth/refresh with valid refresh token returns new pair."""
    # First login to get tokens
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-003",
        "device_name": "刷新测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # Now refresh
    res = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["access_token"] is not None
    assert body["data"]["refresh_token"] is not None


@pytest.mark.asyncio
async def test_car_refresh_replay_detected(async_client: AsyncClient, car_login_setup):
    """Using the same refresh token twice triggers replay detection."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-004",
        "device_name": "重放测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # First refresh — OK
    res1 = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res1.status_code == 200

    # Second refresh with same token — replay detected
    res2 = await async_client.post("/v1/api/car/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res2.status_code == 401
    assert res2.json()["msg"] == "token_replayed"


@pytest.mark.asyncio
async def test_car_logout(async_client: AsyncClient, car_login_setup):
    """POST /v1/api/car/auth/logout revokes refresh token."""
    login_res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": car_login_setup["phone"],
        "device_id": "TEST-DEV-005",
        "device_name": "登出测试",
        "device_type": "car",
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # Logout
    res = await async_client.post("/v1/api/car/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert res.status_code == 200
    assert res.json()["code"] == 0
