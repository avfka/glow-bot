"""Routine tracking business logic."""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class TrackingResult:
    tracking: Any
    streak: int
    new_achievements: list[str] = field(default_factory=list)


def calculate_streak(
    *,
    morning_done: bool,
    evening_done: bool,
    current_streak: int,
    yesterday_streak: int,
    yesterday_complete: bool,
) -> int:
    if morning_done and evening_done:
        return (yesterday_streak + 1) if yesterday_complete else max(current_streak, 1)
    return yesterday_streak if yesterday_complete else 0


async def save_tracking_status(
    session: "AsyncSession",
    user_id: int,
    morning_done: bool,
    evening_done: bool,
    *,
    update_rewards: bool = True,
    commit: bool = True,
) -> TrackingResult:
    from database.repositories.gamification import (
        check_and_grant_streak_achievements,
        upsert_user_league,
    )
    from database.repositories.tracking import (
        get_today_tracking,
        get_tracking_by_date,
        upsert_tracking,
    )

    today_tracking = await get_today_tracking(session, user_id)
    yesterday = date.today() - timedelta(days=1)
    yesterday_tracking = await get_tracking_by_date(session, user_id, yesterday)

    yesterday_complete = bool(
        yesterday_tracking
        and yesterday_tracking.morning_done
        and yesterday_tracking.evening_done
    )
    streak = calculate_streak(
        morning_done=morning_done,
        evening_done=evening_done,
        current_streak=today_tracking.streak_days if today_tracking else 0,
        yesterday_streak=yesterday_tracking.streak_days if yesterday_tracking else 0,
        yesterday_complete=yesterday_complete,
    )

    tracking = await upsert_tracking(
        session=session,
        user_id=user_id,
        morning_done=morning_done,
        evening_done=evening_done,
        streak_days=streak,
        commit=False,
    )

    new_achievements: list[str] = []
    if update_rewards and morning_done and evening_done:
        new_achievements = await check_and_grant_streak_achievements(
            session, user_id, streak, commit=False
        )
        await upsert_user_league(session, user_id, streak, commit=False)

    if commit:
        await session.commit()

    return TrackingResult(
        tracking=tracking,
        streak=streak,
        new_achievements=new_achievements,
    )
