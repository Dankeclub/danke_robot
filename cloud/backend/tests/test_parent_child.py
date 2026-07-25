"""Tests for the parent_child table."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.child import Child
from app.models.family import Family
from app.models.parent import ParentAccount
from app.models.parent_child import ParentChild


async def test_create_parent_child(db_session):
    """A parent-child binding can be inserted and gets a UUID and timestamps."""
    family = Family(name="小宇的家")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:test001",
        phone_masked="138****8000",
    )
    db_session.add(parent)
    await db_session.flush()

    pc = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    db_session.add(pc)
    await db_session.commit()
    await db_session.refresh(pc)

    assert pc.id is not None
    assert isinstance(pc.id, uuid.UUID)
    assert pc.status == "active"
    assert pc.is_default is False
    assert pc.created_at is not None
    assert pc.updated_at is not None


async def test_parent_child_unique_constraint(db_session):
    """Duplicate (parent_id, child_id) violates unique constraint."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="测试孩子")
    db_session.add(child)
    await db_session.flush()

    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:test002",
        phone_masked="138****8000",
    )
    db_session.add(parent)
    await db_session.flush()

    pc1 = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    pc2 = ParentChild(
        parent_id=parent.id,
        family_id=family.id,
        child_id=child.id,
    )
    db_session.add(pc1)
    db_session.add(pc2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
