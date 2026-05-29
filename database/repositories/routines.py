from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Routine, RoutineProduct
from database.repositories.common import finish_write, persist


async def get_latest_routine(
    session: AsyncSession, user_id: int
) -> Optional[Routine]:
    result = await session.execute(
        select(Routine)
        .where(Routine.user_id == user_id)
        .order_by(Routine.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_routine(
    session: AsyncSession,
    user_id: int,
    morning_steps: list,
    evening_steps: list,
    reason_for_change: Optional[str] = None,
    *,
    commit: bool = True,
) -> Routine:
    routine = Routine(
        user_id=user_id,
        morning_steps=morning_steps,
        evening_steps=evening_steps,
        reason_for_change=reason_for_change,
    )
    session.add(routine)
    return await persist(session, routine, commit)


async def get_routine_products(session: AsyncSession, user_id: int) -> dict:
    result = await session.execute(
        select(RoutineProduct).where(RoutineProduct.user_id == user_id)
    )
    items = result.scalars().all()
    return {f"{r.period}_{r.step_index}": r.product_name for r in items}


async def set_routine_product(
    session: AsyncSession,
    user_id: int,
    period: str,
    step_index: int,
    product_name: str,
    *,
    commit: bool = True,
) -> None:
    result = await session.execute(
        select(RoutineProduct).where(
            RoutineProduct.user_id == user_id,
            RoutineProduct.period == period,
            RoutineProduct.step_index == step_index,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.product_name = product_name
    else:
        session.add(
            RoutineProduct(
                user_id=user_id,
                period=period,
                step_index=step_index,
                product_name=product_name,
            )
        )
    await finish_write(session, commit)
