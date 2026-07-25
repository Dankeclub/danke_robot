"""Tests for the child table."""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.child import Child
from app.models.family import Family


async def test_create_child(db_session):
    """A child belongs to a family and gets a UUID and timestamps."""
    family = Family(name="小宇的家")
    db_session.add(family)
    await db_session.flush()

    child = Child(
        family_id=family.id,
        nickname="小宇",
        birth_date=date(2019, 6, 1),
        gender="boy",
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    assert child.id is not None
    assert isinstance(child.id, uuid.UUID)
    assert child.family_id == family.id
    assert child.nickname == "小宇"
    assert child.created_at is not None
    assert child.updated_at is not None


async def test_child_family_fk_violation(db_session):
    """Inserting a child without a valid family_id raises IntegrityError."""
    child = Child(family_id=uuid.uuid4(), nickname="孤儿")
    db_session.add(child)

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_child_nullable_fields(db_session):
    """avatar_url, birth_date, and gender should all be nullable."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="测试")
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    assert child.avatar_url is None
    assert child.birth_date is None
    assert child.gender is None


async def test_child_gender_check_constraint(db_session):
    """Inserting an invalid gender value raises IntegrityError."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(
        family_id=family.id,
        nickname="测试",
        gender="invalid",
    )
    db_session.add(child)

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_child_gender_valid_values(db_session):
    """All three valid gender values should be accepted."""
    family = Family(name="性别测试家庭")
    db_session.add(family)
    await db_session.flush()

    for gender in ("boy", "girl", "unknown", None):
        child = Child(
            family_id=family.id,
            nickname=f"child-{gender or 'none'}",
            gender=gender,
        )
        db_session.add(child)
    await db_session.commit()
