"""Parent behavior business logic — focus, posture, location, insights."""

import uuid as _uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import BehaviorEvent
from app.parent.service import verify_parent_access


def _period_days(period: str) -> int:
    return {"day": 1, "week": 7, "month": 30}.get(period, 7)


async def _compute_daily_scores(
    db: AsyncSession, child_uuid, event_type: str, days: int,
) -> tuple[int, list[dict]]:
    """Return average score and daily series for an event type over N days."""
    cutoff = date.today() - timedelta(days=days - 1)
    today = date.today()

    result = await db.execute(
        select(
            func.date(BehaviorEvent.recorded_at).label("d"),
            func.avg(BehaviorEvent.score).label("avg_score"),
        )
        .where(
            BehaviorEvent.child_id == child_uuid,
            BehaviorEvent.event_type == event_type,
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
        .group_by(func.date(BehaviorEvent.recorded_at))
        .order_by(func.date(BehaviorEvent.recorded_at))
    )
    rows = result.all()

    score_map: dict[str, float] = {}
    total = 0.0
    count = 0
    for d, avg in rows:
        d_str = d.isoformat() if isinstance(d, date) else str(d)
        score_map[d_str] = float(avg) if avg is not None else 0.0
        total += float(avg) if avg is not None else 0.0
        count += 1

    overall = int(total / count) if count > 0 else 0

    series = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        d_str = d.isoformat()
        series.append({"date": d, "score": int(score_map.get(d_str, 0))})

    return overall, series


async def get_focus(
    db: AsyncSession, parent_id: str, child_id: str, period: str = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    child_uuid = _uuid.UUID(child_id)
    days = _period_days(period)
    score, series = await _compute_daily_scores(db, child_uuid, "focus", days)

    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_uuid,
            BehaviorEvent.event_type == "focus",
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    distract_count = sum(1 for p in payloads if p.get("is_distracted"))
    max_focus = max(
        (p.get("focus_duration_seconds", 0) for p in payloads), default=0,
    )
    focus_pct = int(
        sum(1 for p in payloads if not p.get("is_distracted"))
        / max(len(payloads), 1) * 100,
    )
    interrupt_count = sum(1 for p in payloads if p.get("interrupted"))
    return {
        "period": period, "score": score, "change_percent": 0,
        "stats": [
            {"label": "分散次数", "value": distract_count, "unit": "次"},
            {"label": "最长专注", "value": round(max_focus / 60, 1), "unit": "min"},
            {"label": "专注占比", "value": focus_pct, "unit": "%"},
            {"label": "打断次数", "value": interrupt_count, "unit": "次"},
        ],
        "daily_series": series,
    }


async def get_posture(
    db: AsyncSession, parent_id: str, child_id: str, period: str = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    child_uuid = _uuid.UUID(child_id)
    days = _period_days(period)
    score, series = await _compute_daily_scores(db, child_uuid, "posture", days)

    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_uuid,
            BehaviorEvent.event_type == "posture",
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    reminder = sum(1 for p in payloads if p.get("reminder_sent"))
    good = sum(1 for p in payloads if p.get("posture_label") == "good")
    slight = sum(1 for p in payloads if p.get("posture_label") == "slight_tilt")
    bad = sum(1 for p in payloads if p.get("posture_label") == "obvious_slant")
    total = max(len(payloads), 1)
    return {
        "period": period, "score": score, "change_percent": 0,
        "reminder_count": reminder,
        "distribution": [
            {"label": "标准坐姿", "percent": round(good / total * 100)},
            {"label": "轻微倾斜", "percent": round(slight / total * 100)},
            {"label": "明显歪斜", "percent": round(bad / total * 100)},
        ],
        "weekly_series": series,
    }


async def get_location(
    db: AsyncSession, parent_id: str, child_id: str, period: str = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    child_uuid = _uuid.UUID(child_id)
    days = _period_days(period)
    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent.payload)
        .where(
            BehaviorEvent.child_id == child_uuid,
            BehaviorEvent.event_type.in_(["location", "zone"]),
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
    )
    payloads = [r[0] for r in raw.all() if r[0]]
    zone_counts: dict[str, int] = {}
    for p in payloads:
        zone = p.get("zone_name", "未知")
        zone_counts[zone] = zone_counts.get(zone, 0) + 1
    total = max(len(payloads), 1)
    distribution = [
        {"zone": z, "percent": round(c / total * 100)}
        for z, c in sorted(zone_counts.items(), key=lambda x: -x[1])
    ]
    return {
        "period": period,
        "active_zones_count": len(zone_counts),
        "distribution": distribution,
        "anomaly_detected": False,
    }


async def get_insights(
    db: AsyncSession, parent_id: str, child_id: str, period: str = "week",
) -> dict | None:
    if not await verify_parent_access(db, parent_id, child_id):
        return None
    child_uuid = _uuid.UUID(child_id)
    days = _period_days(period)
    cutoff = date.today() - timedelta(days=days - 1)
    raw = await db.execute(
        select(BehaviorEvent)
        .where(
            BehaviorEvent.child_id == child_uuid,
            BehaviorEvent.event_type.in_(["focus", "posture"]),
            func.date(BehaviorEvent.recorded_at) >= cutoff,
        )
        .order_by(BehaviorEvent.recorded_at.desc())
        .limit(10)
    )
    events = raw.scalars().all()
    items = []
    for e in events:
        p = e.payload if isinstance(e.payload, dict) else {}
        insight = p.get("insight")
        if insight:
            items.append({
                "insight_id": str(e.id),
                "type": e.event_type,
                "title": insight.get("title", ""),
                "description": insight.get("description", ""),
                "tags": [
                    {"text": t.get("text", ""), "cls": t.get("cls", "")}
                    for t in insight.get("tags", [])
                ],
                "occurred_at": e.recorded_at,
            })
    return {"items": items}
