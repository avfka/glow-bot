from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Achievement, User, UserLeague
from database.repositories.common import finish_write
from database.repositories.tracking import get_today_tracking, get_tracking_by_date

ACHIEVEMENT_META = {
    "first_analysis": ("🔍", "Первый анализ", "Прошла первый анализ кожи"),
    "streak_3": ("🔥", "3 дня подряд", "Выполняла рутину 3 дня подряд"),
    "streak_7": ("⚡", "Неделя без пропусков", "7 дней стрика"),
    "streak_30": ("🏆", "Месяц!", "30 дней стрика"),
    "products_3": ("🧴", "Коллекционер", "Добавила 3 продукта"),
    "scan_3": ("🔬", "Эксперт состава", "Сканировала 3 продукта"),
    "routine_updated": ("✨", "Обновление рутины", "Обновила рутину с AI"),
}

LEAGUE_CONFIG = [
    ("diamond", "💎 Бриллиант", 90),
    ("platinum", "🏆 Платина", 30),
    ("gold", "🥇 Золото", 14),
    ("silver", "🥈 Серебро", 7),
    ("bronze", "🥉 Бронза", 0),
]


async def get_user_achievements(session: AsyncSession, user_id: int) -> list[str]:
    result = await session.execute(
        select(Achievement.code).where(Achievement.user_id == user_id)
    )
    return [row[0] for row in result.all()]


async def grant_achievement(
    session: AsyncSession,
    user_id: int,
    code: str,
    *,
    commit: bool = True,
) -> bool:
    existing = await session.execute(
        select(Achievement).where(
            Achievement.user_id == user_id,
            Achievement.code == code,
        )
    )
    if existing.scalar_one_or_none():
        return False
    session.add(Achievement(user_id=user_id, code=code))
    await finish_write(session, commit)
    return True


async def check_and_grant_streak_achievements(
    session: AsyncSession,
    user_id: int,
    streak: int,
    *,
    commit: bool = True,
) -> list[str]:
    new_achievements = []
    milestones = [("streak_3", 3), ("streak_7", 7), ("streak_30", 30)]
    for code, required in milestones:
        if streak >= required:
            if await grant_achievement(session, user_id, code, commit=commit):
                new_achievements.append(code)
    return new_achievements


def streak_to_league(streak: int) -> tuple[str, str]:
    for code, label, min_days in LEAGUE_CONFIG:
        if streak >= min_days:
            return code, label
    return "bronze", "🥉 Бронза"


def next_league(current_code: str) -> tuple[str, str, int] | None:
    codes = [c for c, _, _ in LEAGUE_CONFIG]
    idx = codes.index(current_code) if current_code in codes else len(codes) - 1
    if idx == 0:
        return None
    next_code, next_label, next_min = LEAGUE_CONFIG[idx - 1]
    return next_code, next_label, next_min


async def upsert_user_league(
    session: AsyncSession,
    user_id: int,
    streak: int,
    *,
    commit: bool = True,
) -> None:
    league_code, _ = streak_to_league(streak)
    today = date.today()
    result = await session.execute(
        select(UserLeague).where(UserLeague.user_id == user_id)
    )
    league = result.scalar_one_or_none()
    if league:
        if league.week_start is None or (today - league.week_start).days >= 7:
            league.weekly_days = 1
            league.week_start = today
        else:
            league.weekly_days = (league.weekly_days or 0) + 1
        league.league = league_code
    else:
        league = UserLeague(
            user_id=user_id,
            league=league_code,
            weekly_days=1,
            week_start=today,
        )
        session.add(league)
    await finish_write(session, commit)


async def get_leaderboard(session: AsyncSession, user_ids: list[int]) -> list[dict]:
    rows = []
    for uid in user_ids:
        tracking = await get_today_tracking(session, uid)
        if not tracking:
            yesterday = date.today() - timedelta(days=1)
            tracking = await get_tracking_by_date(session, uid, yesterday)
        streak = tracking.streak_days if tracking else 0
        user_result = await session.execute(select(User).where(User.user_id == uid))
        user = user_result.scalar_one_or_none()
        league_result = await session.execute(
            select(UserLeague).where(UserLeague.user_id == uid)
        )
        league_obj = league_result.scalar_one_or_none()
        _, league_label = streak_to_league(streak)
        rows.append(
            {
                "user_id": uid,
                "name": user.name if user else "—",
                "streak": streak,
                "weekly_days": league_obj.weekly_days if league_obj else 0,
                "league": league_label,
            }
        )
    rows.sort(key=lambda x: x["weekly_days"], reverse=True)
    return rows
