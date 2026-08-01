"""Integration tests for parent device management API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _device_setup(db_session):
    """Create parent, child, family. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_openid_dev", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="设备测试孩子")
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
async def _device_token(_device_setup) -> str:
    return _device_setup[0]


@pytest.fixture
async def _device_child_id(_device_setup) -> str:
    return _device_setup[1]


@pytest.mark.asyncio
async def test_bind_and_get_device(
    async_client: AsyncClient, _device_token: str, _device_child_id: str,
):
    """POST bind device, then GET returns it."""
    res = await async_client.post(
        f"/v1/api/parent/children/{_device_child_id}/device/bind",
        json={
            "bind_method": "device_code",
            "device_code": "DEV-001",
            "device_name": "小明的车机",
        },
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["device_name"] == "小明的车机"
    assert body["data"]["device_id"] == "DEV-001"

    # Get device
    res = await async_client.get(
        f"/v1/api/parent/children/{_device_child_id}/device",
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["device_id"] == "DEV-001"


@pytest.mark.asyncio
async def test_update_device_name(
    async_client: AsyncClient, _device_token: str, _device_child_id: str,
):
    """PUT device updates name."""
    await async_client.post(
        f"/v1/api/parent/children/{_device_child_id}/device/bind",
        json={"bind_method": "device_code", "device_code": "DEV-002", "device_name": "原名"},
        headers={"Authorization": f"Bearer {_device_token}"},
    )

    res = await async_client.put(
        f"/v1/api/parent/children/{_device_child_id}/device",
        json={"device_name": "新设备名"},
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["device_name"] == "新设备名"


@pytest.mark.asyncio
async def test_unbind_device(
    async_client: AsyncClient, _device_token: str, _device_child_id: str,
):
    """DELETE device unbinds it."""
    await async_client.post(
        f"/v1/api/parent/children/{_device_child_id}/device/bind",
        json={"bind_method": "device_code", "device_code": "DEV-003", "device_name": "待解绑"},
        headers={"Authorization": f"Bearer {_device_token}"},
    )

    res = await async_client.delete(
        f"/v1/api/parent/children/{_device_child_id}/device",
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 200

    res = await async_client.get(
        f"/v1/api/parent/children/{_device_child_id}/device",
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_bind_duplicate_device_fails(
    async_client: AsyncClient, _device_token: str, _device_child_id: str,
):
    """Binding same device_id twice returns 409."""
    await async_client.post(
        f"/v1/api/parent/children/{_device_child_id}/device/bind",
        json={"bind_method": "device_code", "device_code": "DEV-004", "device_name": "设备"},
        headers={"Authorization": f"Bearer {_device_token}"},
    )

    res = await async_client.post(
        f"/v1/api/parent/children/{_device_child_id}/device/bind",
        json={"bind_method": "device_code", "device_code": "DEV-004", "device_name": "重复设备"},
        headers={"Authorization": f"Bearer {_device_token}"},
    )
    assert res.status_code == 409
