from datetime import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Reminder
from database.repositories.common import persist


async def get_reminder(session: AsyncSession, user_id: int) -> Optional[Reminder]:
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_reminder(
    session: AsyncSession,
    user_id: int,
    morning_time: Optional[time],
    evening_time: Optional[time],
    timezone: str,
    active: bool = True,
    *,
    commit: bool = True,
) -> Reminder:
    reminder = await get_reminder(session, user_id)
    if reminder:
        reminder.morning_time = morning_time
        reminder.evening_time = evening_time
        reminder.timezone = timezone
        reminder.active = active
    else:
        reminder = Reminder(
            user_id=user_id,
            morning_time=morning_time,
            evening_time=evening_time,
            timezone=timezone,
            active=active,
        )
        session.add(reminder)
    return await persist(session, reminder, commit)


async def get_all_active_reminders(session: AsyncSession) -> list[Reminder]:
    result = await session.execute(select(Reminder).where(Reminder.active == True))
    return result.scalars().all()
