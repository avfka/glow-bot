"""Product workflows."""
import logging
from dataclasses import dataclass

from database import async_session_factory
from database.repositories.products import add_user_product, get_active_products
from database.repositories.profiles import get_latest_profile
from database.repositories.routines import create_routine
from services import get_analyzer

logger = logging.getLogger(__name__)


@dataclass
class AddProductResult:
    product_name: str
    product_type: str
    time_of_use: str
    routine_updated: bool = False


async def add_product_and_refresh_routine(
    *,
    user_id: int,
    product_name: str,
    product_type: str,
    time_of_use: str,
) -> AddProductResult:
    async with async_session_factory() as session:
        await add_user_product(
            session=session,
            user_id=user_id,
            product_name=product_name,
            product_type=product_type,
            time_of_use=time_of_use,
            commit=False,
        )

        products = await get_active_products(session, user_id)
        profile = await get_latest_profile(session, user_id)
        await session.commit()

    routine_updated = False
    if profile:
        try:
            analyzer = get_analyzer()
            products_for_ai = [
                {
                    "product_name": product.product_name,
                    "product_type": product.product_type,
                    "time_of_use": product.time_of_use,
                }
                for product in products
            ]
            routine_result = await analyzer.generate_routine(
                profile={
                    "skin_type": profile.skin_type,
                    "skin_problems": profile.skin_problems or [],
                    "allergies": profile.allergies,
                    "budget": profile.budget,
                    "goal": profile.goal,
                    "age": profile.age,
                },
                user_products=products_for_ai,
            )
            async with async_session_factory() as session:
                await create_routine(
                    session=session,
                    user_id=user_id,
                    morning_steps=routine_result.morning_routine,
                    evening_steps=routine_result.evening_routine,
                    reason_for_change=f"Добавлен продукт: {product_name}",
                    commit=False,
                )
                await session.commit()
            routine_updated = True
        except Exception as exc:
            logger.error("Routine update error for user %s: %s", user_id, exc, exc_info=True)

    return AddProductResult(
        product_name=product_name,
        product_type=product_type,
        time_of_use=time_of_use,
        routine_updated=routine_updated,
    )
