"""Integration tests for parent learning config API."""

import pytest
from httpx import AsyncClient

from app.auth.security import create_parent_access_token
from app.models.child import Child
from app.models.config import LearningModuleConfig
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def _config_setup(db_session):
    """Create parent, child, seed 6 module configs. Return (token, child_id)."""
    parent = ParentAccount(wx_openid="test_cfg", status="active")
    db_session.add(parent)
    await db_session.flush()

    family = Family(name="配置测试")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="配置孩子")
    db_session.add(child)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, child_id=child.id, family_id=family.id,
        status="active", is_default=True,
    )
    db_session.add(pc)

    for mod in ["science", "math", "english", "poems", "music", "quiz"]:
        cfg = LearningModuleConfig(
            child_id=child.id, module=mod, enabled=True, batch_size=10,
        )
        db_session.add(cfg)

    await db_session.commit()

    token = create_parent_access_token(parent_id=str(parent.id))
    return token, str(child.id)


@pytest.fixture
async def _cfg_token(_config_setup) -> str:
    return _config_setup[0]


@pytest.fixture
async def _cfg_child_id(_config_setup) -> str:
    return _config_setup[1]


@pytest.mark.asyncio
async def test_get_learning_config(
    async_client: AsyncClient, _cfg_token: str, _cfg_child_id: str,
):
    """GET config returns 6 modules."""
    res = await async_client.get(
        f"/v1/api/parent/children/{_cfg_child_id}/learning/config",
        headers={"Authorization": f"Bearer {_cfg_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]) == 6
    modules = {m["module"] for m in body["data"]}
    assert modules == {"science", "math", "english", "poems", "music", "quiz"}


@pytest.mark.asyncio
async def test_update_learning_config(
    async_client: AsyncClient, _cfg_token: str, _cfg_child_id: str,
):
    """PUT config updates module settings."""
    res = await async_client.put(
        f"/v1/api/parent/children/{_cfg_child_id}/learning/config",
        json={
            "modules": [
                {
                    "module": "science",
                    "enabled": True,
                    "difficulty": "advanced",
                    "batch_size": 20,
                },
            ],
        },
        headers={"Authorization": f"Bearer {_cfg_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0

    sci = next(m for m in body["data"] if m["module"] == "science")
    assert sci["enabled"] is True
    assert sci["effective_config"]["difficulty"] == "advanced"
    assert sci["effective_config"]["batch_size"] == 20
    assert sci["effective_config"]["config_version"] == 2


@pytest.mark.asyncio
async def test_config_audit(
    async_client: AsyncClient, _cfg_token: str, _cfg_child_id: str,
):
    """Config changes create audit entries."""
    await async_client.put(
        f"/v1/api/parent/children/{_cfg_child_id}/learning/config",
        json={
            "modules": [
                {"module": "math", "enabled": False, "difficulty": "two_digit_add_subtract"},
            ],
        },
        headers={"Authorization": f"Bearer {_cfg_token}"},
    )

    res = await async_client.get(
        f"/v1/api/parent/children/{_cfg_child_id}/learning/config/audit",
        headers={"Authorization": f"Bearer {_cfg_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert len(body["data"]["items"]) >= 1
    audit = body["data"]["items"][0]
    assert audit["module"] == "math"


@pytest.mark.asyncio
async def test_config_not_found_for_other_parent(
    async_client: AsyncClient, _cfg_child_id: str, db_session,
):
    """Parent cannot access another parent's child config."""
    other = ParentAccount(wx_openid="other_cfg", status="active")
    db_session.add(other)
    await db_session.commit()
    other_token = create_parent_access_token(parent_id=str(other.id))

    res = await async_client.get(
        f"/v1/api/parent/children/{_cfg_child_id}/learning/config",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 404
