"""Integration tests for parent file upload API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token


@pytest.fixture
async def _files_token(db_session):
    from app.models.parent import ParentAccount
    parent = ParentAccount(wx_openid="test_files_p", status="active")
    db_session.add(parent)
    await db_session.commit()
    return create_parent_access_token(parent_id=str(parent.id))


@pytest.mark.asyncio
async def test_init_upload(async_client: AsyncClient, _files_token):
    res = await async_client.post(
        "/v1/api/parent/files/uploads",
        json={
            "purpose": "parent_message_image",
            "file_name": "test.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 1024,
            "sha256": "abc123",
        },
        headers={"Authorization": f"Bearer {_files_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["upload_id"] != ""


@pytest.mark.asyncio
async def test_complete_upload(async_client: AsyncClient, _files_token):
    # Init
    init_res = await async_client.post(
        "/v1/api/parent/files/uploads",
        json={
            "purpose": "parent_message_image",
            "file_name": "test2.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 2048,
            "sha256": "def456",
        },
        headers={"Authorization": f"Bearer {_files_token}"},
    )
    upload_id = init_res.json()["data"]["upload_id"]
    # Complete
    res = await async_client.post(
        f"/v1/api/parent/files/uploads/{upload_id}/complete",
        json={"size_bytes": 2048, "sha256": "def456"},
        headers={"Authorization": f"Bearer {_files_token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "available"


@pytest.mark.asyncio
async def test_files_require_auth(async_client: AsyncClient):
    res = await async_client.post(
        "/v1/api/parent/files/uploads",
        json={"purpose": "parent_message_image", "file_name": "x.jpg",
              "content_type": "image/jpeg", "size_bytes": 1, "sha256": "x"},
    )
    assert res.status_code == 401
