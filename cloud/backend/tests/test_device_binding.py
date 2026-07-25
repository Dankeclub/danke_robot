"""Tests for the device_binding table."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.child import Child
from app.models.device_binding import DeviceBinding
from app.models.family import Family


async def test_create_device_binding(db_session):
    """A device can be bound to a child and gets a UUID and timestamps."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    binding = DeviceBinding(
        device_id="car_device_001",
        child_id=child.id,
        device_name="客厅车机",
    )
    db_session.add(binding)
    await db_session.commit()
    await db_session.refresh(binding)

    assert binding.id is not None
    assert isinstance(binding.id, uuid.UUID)
    assert binding.device_id == "car_device_001"
    assert binding.child_id == child.id
    assert binding.device_name == "客厅车机"
    assert binding.device_type == "car"
    assert binding.bind_status == "active"
    assert binding.bound_at is not None
    assert binding.created_at is not None
    assert binding.updated_at is not None


async def test_device_id_unique(db_session):
    """Duplicate device_id violates unique constraint."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child_a = Child(family_id=family.id, nickname="小宇")
    child_b = Child(family_id=family.id, nickname="小明")
    db_session.add_all([child_a, child_b])
    await db_session.flush()

    b1 = DeviceBinding(
        device_id="car_device_001",
        child_id=child_a.id,
        device_name="客厅车机",
    )
    b2 = DeviceBinding(
        device_id="car_device_001",
        child_id=child_b.id,
        device_name="卧室车机",
    )
    db_session.add(b1)
    db_session.add(b2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_one_active_binding_per_child(db_session):
    """A child can have only one active binding; inactive/revoked are allowed."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    b1 = DeviceBinding(
        device_id="car_device_001",
        child_id=child.id,
        device_name="客厅车机",
    )
    db_session.add(b1)
    await db_session.commit()

    # Second active binding for the same child must fail
    b2 = DeviceBinding(
        device_id="car_device_002",
        child_id=child.id,
        device_name="卧室车机",
    )
    db_session.add(b2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_inactive_binding_does_not_conflict(db_session):
    """A child can have multiple inactive bindings, no partial index conflict."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    b1 = DeviceBinding(
        device_id="car_device_001",
        child_id=child.id,
        device_name="客厅车机",
        bind_status="inactive",
    )
    db_session.add(b1)
    await db_session.commit()

    b2 = DeviceBinding(
        device_id="car_device_002",
        child_id=child.id,
        device_name="卧室车机",
        bind_status="inactive",
    )
    db_session.add(b2)
    await db_session.commit()

    assert b1.id is not None
    assert b2.id is not None


async def test_device_binding_optional_fields(db_session):
    """platform and app_version are nullable."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    binding = DeviceBinding(
        device_id="car_device_001",
        child_id=child.id,
        device_name="客厅车机",
    )
    db_session.add(binding)
    await db_session.commit()
    await db_session.refresh(binding)

    assert binding.platform is None
    assert binding.app_version is None


async def test_device_type_car_or_robot(db_session):
    """Valid device_type values: car, robot."""
    family = Family(name="测试家庭")
    db_session.add(family)
    await db_session.flush()

    child = Child(family_id=family.id, nickname="小宇")
    db_session.add(child)
    await db_session.flush()

    # robot is valid
    binding = DeviceBinding(
        device_id="robot_device_001",
        child_id=child.id,
        device_name="扫地机器人",
        device_type="robot",
    )
    db_session.add(binding)
    await db_session.commit()
    await db_session.refresh(binding)
    assert binding.device_type == "robot"

    # invalid device_type must be rejected by CHECK constraint
    bad = DeviceBinding(
        device_id="bad_device",
        child_id=child.id,
        device_name="坏设备",
        device_type="tablet",
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError):
        await db_session.commit()
