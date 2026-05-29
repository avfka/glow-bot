from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Tracking, User
from database.repositories.common import persist


async def get_today_tracking(session: AsyncSession, user_id: int) -> Optional[Tracking]:
    today = date.today()
    result = await session.execute(
        select(Tracking).where(
            and_(Tracking.user_id == user_id, Tracking.date == today)
        )
    )
    return result.scalar_one_or_none()


async def get_tracking_by_date(
    session: AsyncSession, user_id: int, day: date
) -> Optional[Tracking]:
    result = await session.execute(
        select(Tracking).where(
            and_(Tracking.user_id == user_id, Tracking.date == day)
        )
    )
    return result.scalar_one_or_none()


async def upsert_tracking(
    session: AsyncSession,
    user_id: int,
    morning_done: bool,
    evening_done: bool,
    streak_days: int,
    products_used: Optional[list] = None,
    notes: Optional[str] = None,
    *,
    commit: bool = True,
) -> Tracking:
    today = date.today()
    tracking = await get_today_tracking(session, user_id)
    if tracking:
        tracking.morning_done = morning_done
        tracking.evening_done = evening_done
        tracking.streak_days = streak_days
        if products_used is not None:
            tracking.products_used = products_used
        if notes is not None:
            tracking.notes = notes
    else:
        tracking = Tracking(
            user_id=user_id,
            date=today,
            morning_done=morning_done,
            evening_done=evening_done,
            streak_days=streak_days,
            products_used=products_used or [],
            notes=notes,
        )
        session.add(tracking)
    return await persist(session, tracking, commit)


async def get_current_streak(session: AsyncSession, user_id: int) -> int:
    today = date.today()
    tracking = await get_today_tracking(session, user_id)
    if tracking:
        return tracking.streak_days

    yesterday = today - timedelta(days=1)
    yesterday_tracking = await get_tracking_by_date(session, user_id, yesterday)
    if (
        yesterday_tracking
        and yesterday_tracking.morning_done
        and yesterday_tracking.evening_done
    ):
        return yesterday_tracking.streak_days
    return 0


async def get_streak_leaderboard(
    session: AsyncSession, user_ids: list[int]
) -> list[dict]:
    today = date.today()
    results = []
    for uid in user_ids:
        tracking = await get_today_tracking(session, uid)
        if not tracking:
            yesterday = today - timedelta(days=1)
            tracking = await get_tracking_by_date(session, uid, yesterday)
        streak = tracking.streak_days if tracking else 0
        user_result = await session.execute(select(User).where(User.user_id == uid))
        user = user_result.scalar_one_or_none()
        results.append(
            {
                "user_id": uid,
                "name": user.name if user else "—",
                "streak": streak,
            }
        )
    results.sort(key=lambda x: x["streak"], reverse=True)
    return results
