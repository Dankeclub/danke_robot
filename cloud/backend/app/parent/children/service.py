"""Parent children business logic."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child import Child
from app.models.device_binding import DeviceBinding
from app.models.family import Family
from app.models.parent_child import ParentChild

VALID_GENDERS = {"boy", "girl", "unknown"}


async def list_children(db: AsyncSession, parent_id: str) -> list[dict]:
    """Return all children belonging to a parent, with family info."""
    result = await db.execute(
        select(ParentChild, Child, Family)
        .join(Child, ParentChild.child_id == Child.id)
        .join(Family, Child.family_id == Family.id)
        .where(
            ParentChild.parent_id == parent_id,
            ParentChild.status == "active",
        )
    )
    rows = result.all()

    children = []
    for pc, child, family in rows:
        children.append({
            "child_id": str(child.id),
            "nickname": child.nickname,
            "avatar_url": child.avatar_url,
            "birth_date": child.birth_date.isoformat() if child.birth_date else None,
            "gender": child.gender,
            "family_id": str(family.id),
            "family_name": family.name,
            "is_default": pc.is_default,
        })
    return children


async def get_child_detail(
    db: AsyncSession, parent_id: str, child_id: str,
) -> dict | None:
    """Return child detail with device info, or None if not found/accessible."""
    result = await db.execute(
        select(Child, Family, ParentChild)
        .join(Family, Child.family_id == Family.id)
        .join(
            ParentChild,
            (ParentChild.child_id == Child.id)
            & (ParentChild.parent_id == parent_id),
        )
        .where(Child.id == child_id, ParentChild.status == "active")
    )
    row = result.one_or_none()
    if row is None:
        return None

    child, family, pc = row

    # Look up active device binding
    dev_result = await db.execute(
        select(DeviceBinding).where(
            DeviceBinding.child_id == child.id,
            DeviceBinding.bind_status == "active",
        )
    )
    device = dev_result.scalar_one_or_none()

    device_info = None
    if device:
        device_info = {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "online": False,  # Phase 2: online status not yet tracked
            "bind_status": device.bind_status,
        }

    return {
        "child_id": str(child.id),
        "nickname": child.nickname,
        "avatar_url": child.avatar_url,
        "birth_date": child.birth_date.isoformat() if child.birth_date else None,
        "gender": child.gender,
        "family_id": str(family.id),
        "family_name": family.name,
        "is_default": pc.is_default,
        "device": device_info,
    }


async def create_child(
    db: AsyncSession,
    parent_id: str,
    nickname: str,
    family_id: str | None = None,
    avatar_url: str | None = None,
    birth_date: str | None = None,
    gender: str | None = None,
) -> dict:
    """Create a new child and bind to parent.

    If family_id is not provided, a new family is created automatically.
    """
    from datetime import date as date_cls

    # Validate gender
    if gender is not None and gender not in VALID_GENDERS:
        raise ValueError(f"invalid_gender: {gender}")

    # Resolve or create family
    if family_id and family_id.strip():
        fam_result = await db.execute(
            select(Family).where(Family.id == family_id)
        )
        family = fam_result.scalar_one_or_none()
        if family is None:
            raise ValueError("family_not_found")
    else:
        family = Family(name=nickname + "的家庭")
        db.add(family)
        await db.flush()

    # Create child
    child = Child(
        family_id=family.id,
        nickname=nickname,
        avatar_url=avatar_url,
        birth_date=date_cls.fromisoformat(birth_date) if birth_date else None,
        gender=gender,
    )
    db.add(child)
    await db.flush()

    # Create parent-child binding
    pc = ParentChild(
        parent_id=parent_id,
        child_id=child.id,
        family_id=family.id,
        status="active",
        is_default=True,
    )
    db.add(pc)

    return {
        "child_id": str(child.id),
        "nickname": child.nickname,
        "avatar_url": child.avatar_url,
        "birth_date": child.birth_date.isoformat() if child.birth_date else None,
        "gender": child.gender,
        "family_id": str(family.id),
        "family_name": family.name,
        "is_default": True,
    }


async def update_child(
    db: AsyncSession,
    parent_id: str,
    child_id: str,
    nickname: str,
    avatar_url: str | None = None,
    birth_date: str | None = None,
    gender: str | None = None,
) -> dict | None:
    """Update a child's profile. Returns updated child or None."""
    from datetime import date as date_cls

    # Verify access and capture the binding info
    pc_result = await db.execute(
        select(ParentChild).where(
            ParentChild.parent_id == parent_id,
            ParentChild.child_id == child_id,
            ParentChild.status == "active",
        )
    )
    pc = pc_result.scalar_one_or_none()
    if pc is None:
        return None

    # Validate gender
    if gender is not None and gender not in VALID_GENDERS:
        raise ValueError(f"invalid_gender: {gender}")

    # Fetch child and family
    child_result = await db.execute(
        select(Child).where(Child.id == child_id)
    )
    child = child_result.scalar_one_or_none()
    if child is None:
        return None

    family_result = await db.execute(
        select(Family).where(Family.id == child.family_id)
    )
    family = family_result.scalar_one_or_none()

    child.nickname = nickname
    if avatar_url is not None:
        child.avatar_url = avatar_url
    if birth_date is not None:
        child.birth_date = date_cls.fromisoformat(birth_date)
    if gender is not None:
        child.gender = gender

    await db.flush()

    return {
        "child_id": str(child.id),
        "nickname": child.nickname,
        "avatar_url": child.avatar_url,
        "birth_date": child.birth_date.isoformat() if child.birth_date else None,
        "gender": child.gender,
        "family_id": str(family.id) if family else "",
        "family_name": family.name if family else "",
        "is_default": pc.is_default,
    }


async def unbind_child(
    db: AsyncSession, parent_id: str, child_id: str,
) -> bool:
    """Soft-delete parent-child binding. Returns True if found and deactivated."""
    result = await db.execute(
        select(ParentChild).where(
            ParentChild.parent_id == parent_id,
            ParentChild.child_id == child_id,
            ParentChild.status == "active",
        )
    )
    pc = result.scalar_one_or_none()
    if pc is None:
        return False

    pc.status = "inactive"
    await db.flush()
    return True
