from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
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
