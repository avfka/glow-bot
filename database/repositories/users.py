from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ProductScan, SkinAnalysisHistory, Tracking, User, UserProduct
from database.repositories.common import persist


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    *,
    commit: bool = True,
) -> User:
    user = User(user_id=user_id, name=name)
    session.add(user)
    return await persist(session, user, commit)


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    *,
    commit: bool = True,
) -> User:
    user = await get_user(session, user_id)
    if not user:
        user = await create_user(session, user_id, name, commit=commit)
    return user


async def list_recent_users(session: AsyncSession, limit: int = 20) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def get_user_admin_stats(session: AsyncSession, user_id: int) -> dict:
    products_count = await _count(session, UserProduct.user_id == user_id, UserProduct)
    scans_count = await _count(session, ProductScan.user_id == user_id, ProductScan)
    analyses_count = await _count(
        session, SkinAnalysisHistory.user_id == user_id, SkinAnalysisHistory
    )
    last_tracking = await session.execute(
        select(Tracking)
        .where(Tracking.user_id == user_id)
        .order_by(Tracking.date.desc())
        .limit(1)
    )
    tracking = last_tracking.scalar_one_or_none()
    return {
        "products_count": products_count,
        "scans_count": scans_count,
        "analyses_count": analyses_count,
        "last_tracking_date": tracking.date if tracking else None,
        "streak": tracking.streak_days if tracking else 0,
    }


async def _count(session: AsyncSession, condition, model) -> int:
    result = await session.execute(select(func.count()).select_from(model).where(condition))
    return int(result.scalar_one())
