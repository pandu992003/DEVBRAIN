"""
Dashboard API — aggregated stats for the main UI view.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.recommendation import DashboardStats, DashboardResponse, ActivityPoint
from app.services.event_service import get_events_this_week, get_activity_last_30_days, get_user_events
from app.services.skill_service import get_user_skills

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Aggregated dashboard view: stats, activity timeline, top skills."""
    total_events, recent_events = await get_user_events(db, current_user.id, limit=5)
    events_this_week = await get_events_this_week(db, current_user.id)
    skills = await get_user_skills(db, current_user.id)
    activity = await get_activity_last_30_days(db, current_user.id)

    active_domains = len({s.domain for s in skills})
    top_tech = skills[0].technology if skills else None
    overall_score = (sum(s.score for s in skills) / len(skills)) if skills else 0.0

    # Determine connected sources from events
    _, all_events = await get_user_events(db, current_user.id, limit=1000)
    connected_sources = list({e.source.value for e in all_events})

    stats = DashboardStats(
        total_events=total_events,
        events_this_week=events_this_week,
        active_domains=active_domains,
        top_technology=top_tech,
        overall_skill_score=round(overall_score, 1),
        learning_streak_days=_calculate_streak(activity),
        connected_sources=connected_sources,
    )

    top_skills = [
        {"technology": s.technology, "domain": s.domain, "score": round(s.score, 1), "level": s.level}
        for s in skills[:6]
    ]

    recent = [
        {
            "id": e.id,
            "topic": e.topic,
            "technology": e.technology,
            "domain": e.domain,
            "source": e.source.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in recent_events
    ]

    return DashboardResponse(
        user_id=current_user.id,
        username=current_user.username,
        stats=stats,
        activity_last_30_days=[ActivityPoint(**a) for a in activity],
        top_skills=top_skills,
        recent_events=recent,
    )


def _calculate_streak(activity: list[dict]) -> int:
    """Count consecutive days with at least one event (working backwards from today)."""
    from datetime import datetime, timedelta, timezone

    if not activity:
        return 0

    days_with_events = {a["date"] for a in activity}
    streak = 0
    today = datetime.now(timezone.utc).date()

    for i in range(30):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day_str in days_with_events:
            streak += 1
        else:
            break

    return streak
