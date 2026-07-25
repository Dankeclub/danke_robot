"""Tests for the family table."""

import uuid

from app.models.family import Family


async def test_create_family(db_session):
    """A family can be inserted and gets a UUID and timestamps."""
    family = Family(name="小宇的家")
    db_session.add(family)
    await db_session.commit()
    await db_session.refresh(family)

    assert family.id is not None
    assert isinstance(family.id, uuid.UUID)
    assert family.name == "小宇的家"
    assert family.created_at is not None
    assert family.updated_at is not None
