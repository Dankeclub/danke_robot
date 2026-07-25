"""Tests for the parent_account table."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.parent import ParentAccount


async def test_create_parent_account(db_session):
    """A parent account can be inserted and gets a UUID and timestamps."""
    parent = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:abc123",
        phone_masked="138****8000",
        nickname="妈妈",
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    assert parent.id is not None
    assert isinstance(parent.id, uuid.UUID)
    assert parent.created_at is not None
    assert parent.updated_at is not None
    assert parent.status == "active"


async def test_phone_hash_unique(db_session):
    """Duplicate phone_hash values violate the unique constraint."""
    parent_a = ParentAccount(
        phone_e164="+8613800138000",
        phone_hash="sha256:same",
        phone_masked="138****8000",
    )
    parent_b = ParentAccount(
        phone_e164="+8613900139000",
        phone_hash="sha256:same",
        phone_masked="139****9000",
    )
    db_session.add(parent_a)
    db_session.add(parent_b)

    with pytest.raises(IntegrityError):
        await db_session.commit()
