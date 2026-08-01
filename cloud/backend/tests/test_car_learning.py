"""Integration tests for car learning endpoints — park, sessions, batches, completion."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.auth.security import hash_phone
from app.models.child import Child
from app.models.config import LearningModuleConfig
from app.models.content import MathQuestion
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


@pytest.fixture
async def learning_setup(db_session):
    """Create test data: family, child, parent, configs, content."""
    family = Family(name="学习测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="学习测试孩子")
    db_session.add(child)
    await db_session.flush()

    phone = "+8613800138100"
    parent = ParentAccount(
        phone_e164=phone,
        phone_hash=hash_phone(phone),
        phone_masked="138****8100",
        status="active",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id, family_id=family.id,
        child_id=child.id, is_default=True,
    )
    db_session.add(pc)

    # Seed math config
    db_session.add(LearningModuleConfig(
        child_id=child.id, module="math",
        difficulty="within_10_add_subtract", batch_size=3,
        enabled=True, config_version=1,
    ))

    # Seed math content (3 questions, matching batch_size=3)
    math_items = [
        ("3 + 4 = ?", "6", "7", "8", "9", "B"),
        ("8 - 3 = ?", "4", "6", "5", "7", "C"),
        ("2 + 5 = ?", "7", "6", "8", "9", "A"),
    ]
    for question, a, b, c, d, correct in math_items:
        db_session.add(MathQuestion(
            difficulty="within_10_add_subtract",
            question=question,
            option_a=a, option_b=b, option_c=c, option_d=d,
            correct_option_id=correct,
            status="published",
        ))

    await db_session.commit()

    return {"phone": phone, "child_id": str(child.id), "family_id": str(family.id)}


async def _login(async_client: AsyncClient, phone: str) -> str:
    """Helper: login and return access_token."""
    res = await async_client.post("/v1/api/car/auth/login", json={
        "phone": phone,
        "device_id": f"TEST-LEARN-{uuid.uuid4().hex[:6]}",
        "device_name": "学习测试设备",
        "device_type": "car",
    })
    assert res.status_code == 200
    return res.json()["data"]["access_token"]


# ── Test 1: Learning Park ──────────────────────────────────


@pytest.mark.asyncio
async def test_learning_park_returns_modules(
    async_client: AsyncClient, learning_setup,
):
    """GET /learning/park returns 6 module configs."""
    token = await _login(async_client, learning_setup["phone"])

    res = await async_client.get(
        "/v1/api/car/learning/park",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    modules = body["data"]["modules"]
    assert len(modules) == 6

    # Math module should have our explicit config
    math = next(m for m in modules if m["module"] == "math")
    assert math["difficulty"] == "within_10_add_subtract"
    assert math["batch_size"] == 3
    assert math["enabled_for_today_task"] is True

    # All modules should have labels
    for m in modules:
        assert m["module_label"]


# ── Test 2: Session + Batch content delivery ───────────────


@pytest.mark.asyncio
async def test_create_session_and_batch_success(
    async_client: AsyncClient, learning_setup,
):
    """Create a learning session then request a batch of content."""
    token = await _login(async_client, learning_setup["phone"])

    # 2a. Create session
    res = await async_client.post(
        "/v1/api/car/learning/math/sessions",
        json={"source": "free_learning"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    session_id = body["data"]["session_id"]
    assert body["data"]["module"] == "math"
    assert body["data"]["status"] == "active"
    assert body["data"]["config_snapshot"]["batch_size"] == 3

    # 2b. Request batch
    res = await async_client.post(
        f"/v1/api/car/learning/math/sessions/{session_id}/batches",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["batch_id"]
    assert data["module"] == "math"
    items = data["items"]
    assert len(items) == 3

    # Each item has a content_snapshot with answer data
    for item in items:
        snap = item["content_snapshot"]
        assert snap["correct_option_id"] in ("A", "B", "C", "D")
        assert snap["question"]


@pytest.mark.asyncio
async def test_second_batch_returns_next_sequence(
    async_client: AsyncClient, learning_setup,
):
    """Requesting another batch creates a new batch with bumped sequence_no."""
    token = await _login(async_client, learning_setup["phone"])

    # Create session
    res = await async_client.post(
        "/v1/api/car/learning/math/sessions",
        json={"source": "free_learning"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = res.json()["data"]["session_id"]

    # First batch
    res1 = await async_client.post(
        f"/v1/api/car/learning/math/sessions/{session_id}/batches",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    batch_id_1 = res1.json()["data"]["batch_id"]

    # Second batch — new sequence, new batch
    res2 = await async_client.post(
        f"/v1/api/car/learning/math/sessions/{session_id}/batches",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.json()["data"]["batch_id"] != batch_id_1
    assert len(res2.json()["data"]["items"]) > 0


# ── Test 3: Session completion ─────────────────────────────


@pytest.mark.asyncio
async def test_complete_session_with_answers(
    async_client: AsyncClient, learning_setup,
):
    """Submit answers, then request completion check."""
    token = await _login(async_client, learning_setup["phone"])

    # Create session
    res = await async_client.post(
        "/v1/api/car/learning/math/sessions",
        json={"source": "free_learning"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = res.json()["data"]["session_id"]

    # Get batch
    res = await async_client.post(
        f"/v1/api/car/learning/math/sessions/{session_id}/batches",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    batch_id = res.json()["data"]["batch_id"]
    items = res.json()["data"]["items"]

    # Submit answer events for each item
    now = datetime.now(UTC).isoformat()
    events = []
    for item in items:
        snap = item["content_snapshot"]
        events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": "answer_submitted",
            "module": "math",
            "timestamp": now,
            "payload": {
                "session_id": session_id,
                "batch_id": batch_id,
                "question_id": item["content_id"],
                "selected_option_id": snap["correct_option_id"],  # all correct
                "answer_duration_ms": 3000,
            },
        })

    res = await async_client.post(
        "/v1/api/car/telemetry/events:batch",
        json={"events": events},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["accepted"] == 3

    # Complete session
    res = await async_client.post(
        f"/v1/api/car/telemetry/sessions/{session_id}/complete",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "completed"
