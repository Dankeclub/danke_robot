"""Integration tests for parent children management API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.parent import ParentAccount


@pytest.fixture
async def _parent_token(db_session) -> str:
    """Create a parent account and return a valid JWT."""
    parent = ParentAccount(
        wx_openid="test_openid_children",
        status="active",
    )
    db_session.add(parent)
    await db_session.flush()
    token = create_parent_access_token(parent_id=str(parent.id))
    await db_session.commit()
    return token


@pytest.mark.asyncio
async def test_list_children_empty(async_client: AsyncClient, _parent_token: str):
    """GET /parent/children returns empty list for parent with no children."""
    res = await async_client.get(
        "/v1/api/parent/children",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_create_and_list_children(async_client: AsyncClient, _parent_token: str):
    """POST /parent/children creates a child, GET returns it in list."""
    # Create child
    res = await async_client.post(
        "/v1/api/parent/children",
        json={"nickname": "小明", "family_id": None},
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "小明"
    child_id = body["data"]["child_id"]

    # List should contain the child
    res = await async_client.get(
        "/v1/api/parent/children",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 1
    assert body["data"][0]["nickname"] == "小明"
    assert body["data"][0]["child_id"] == child_id


@pytest.mark.asyncio
async def test_get_child_detail(async_client: AsyncClient, _parent_token: str):
    """GET /parent/children/{id} returns child detail."""
    # Create child
    res = await async_client.post(
        "/v1/api/parent/children",
        json={"nickname": "小红", "gender": "girl", "family_id": None},
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    child_id = res.json()["data"]["child_id"]

    # Get detail
    res = await async_client.get(
        f"/v1/api/parent/children/{child_id}",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "小红"
    assert body["data"]["gender"] == "girl"
    assert body["data"]["child_id"] == child_id


@pytest.mark.asyncio
async def test_update_child(async_client: AsyncClient, _parent_token: str):
    """PUT /parent/children/{id} updates child profile."""
    # Create child
    res = await async_client.post(
        "/v1/api/parent/children",
        json={"nickname": "原名字", "family_id": None},
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    child_id = res.json()["data"]["child_id"]

    # Update
    res = await async_client.put(
        f"/v1/api/parent/children/{child_id}",
        json={"nickname": "新名字", "gender": "boy"},
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "新名字"
    assert body["data"]["gender"] == "boy"


@pytest.mark.asyncio
async def test_delete_child(async_client: AsyncClient, _parent_token: str):
    """DELETE /parent/children/{id} unbinds child."""
    # Create child
    res = await async_client.post(
        "/v1/api/parent/children",
        json={"nickname": "待解绑", "family_id": None},
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    child_id = res.json()["data"]["child_id"]

    # Delete
    res = await async_client.delete(
        f"/v1/api/parent/children/{child_id}",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 200
    assert res.json()["code"] == 0

    # Should not appear in list
    res = await async_client.get(
        "/v1/api/parent/children",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.json()["data"] == []


@pytest.mark.asyncio
async def test_child_not_found(async_client: AsyncClient, _parent_token: str):
    """GET /parent/children/{nonexistent} returns 404."""
    res = await async_client.get(
        "/v1/api/parent/children/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {_parent_token}"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """Requests without token return 401."""
    res = await async_client.get("/v1/api/parent/children")
    assert res.status_code == 401

    res = await async_client.post(
        "/v1/api/parent/children",
        json={"nickname": "test", "family_id": None},
    )
    assert res.status_code == 401
