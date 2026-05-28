from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User, UserProfileVersion, SkinAnalysisHistory, Routine,
    Tracking, UserProduct, Reminder, SkinDiary,
    ProductCatalog, ProductScan, IngredientsLibrary,
)


# ── Users ────────────────────────────────────────────────────────────────────

async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_id: int, name: str) -> User:
    user = User(user_id=user_id, name=name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(session: AsyncSession, user_id: int, name: str) -> User:
    user = await get_user(session, user_id)
    if not user:
        user = await create_user(session, user_id, name)
    return user


# ── Profile versions (immutable, versioned) ──────────────────────────────────

async def get_latest_profile(session: AsyncSession, user_id: int) -> Optional[UserProfileVersion]:
    result = await session.execute(
        select(UserProfileVersion)
        .where(UserProfileVersion.user_id == user_id)
        .order_by(UserProfileVersion.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_profile_version(
    session: AsyncSession,
    user_id: int,
    skin_type: str,
    skin_problems: list,
    allergies: Optional[str],
    budget: str,
    goal: str,
    age: int,
    changed_by: str = "user",
    change_reason: Optional[str] = None,
) -> UserProfileVersion:
    profile = UserProfileVersion(
        user_id=user_id,
        skin_type=skin_type,
        skin_problems=skin_problems,
        allergies=allergies,
        budget=budget,
        goal=goal,
        age=age,
        changed_by=changed_by,
        change_reason=change_reason,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


# ── Skin analysis history ────────────────────────────────────────────────────

async def save_skin_analysis(
    session: AsyncSession,
    user_id: int,
    photo_path: Optional[str],
    ai_raw_response: dict,
    ai_detected_problems: list,
    user_confirmed_problems: Optional[list] = None,
    user_corrections: bool = False,
    skin_score: Optional[dict] = None,
) -> SkinAnalysisHistory:
    record = SkinAnalysisHistory(
        user_id=user_id,
        photo_path=photo_path,
        ai_raw_response=ai_raw_response,
        ai_detected_problems=ai_detected_problems,
        user_confirmed_problems=user_confirmed_problems,
        user_corrections=user_corrections,
        skin_score=skin_score,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def update_analysis_user_confirmation(
    session: AsyncSession,
    analysis_id: int,
    user_confirmed_problems: list,
    user_corrections: bool,
) -> None:
    result = await session.execute(
        select(SkinAnalysisHistory).where(SkinAnalysisHistory.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis:
        analysis.user_confirmed_problems = user_confirmed_problems
        analysis.user_corrections = user_corrections
        await session.commit()


# ── Routines (versioned) ─────────────────────────────────────────────────────

async def get_latest_routine(session: AsyncSession, user_id: int) -> Optional[Routine]:
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
) -> Routine:
    routine = Routine(
        user_id=user_id,
        morning_steps=morning_steps,
        evening_steps=evening_steps,
        reason_for_change=reason_for_change,
    )
    session.add(routine)
    await session.commit()
    await session.refresh(routine)
    return routine


# ── Tracking ─────────────────────────────────────────────────────────────────

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
    await session.commit()
    await session.refresh(tracking)
    return tracking


async def get_current_streak(session: AsyncSession, user_id: int) -> int:
    today = date.today()
    tracking = await get_today_tracking(session, user_id)
    if tracking:
        return tracking.streak_days
    # Check yesterday
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    yesterday_tracking = await get_tracking_by_date(session, user_id, yesterday)
    if yesterday_tracking and yesterday_tracking.morning_done and yesterday_tracking.evening_done:
        return yesterday_tracking.streak_days
    return 0


async def get_streak_leaderboard(session: AsyncSession, user_ids: list[int]) -> list[dict]:
    today = date.today()
    from datetime import timedelta
    results = []
    for uid in user_ids:
        tracking = await get_today_tracking(session, uid)
        if not tracking:
            yesterday = today - timedelta(days=1)
            tracking = await get_tracking_by_date(session, uid, yesterday)
        streak = tracking.streak_days if tracking else 0
        user = await get_user(session, uid)
        results.append({"user_id": uid, "name": user.name if user else "—", "streak": streak})
    results.sort(key=lambda x: x["streak"], reverse=True)
    return results


# ── User products ─────────────────────────────────────────────────────────────

async def get_active_products(session: AsyncSession, user_id: int) -> list[UserProduct]:
    result = await session.execute(
        select(UserProduct).where(
            and_(UserProduct.user_id == user_id, UserProduct.status == "active")
        ).order_by(UserProduct.added_at.asc())
    )
    return result.scalars().all()


async def add_user_product(
    session: AsyncSession,
    user_id: int,
    product_name: str,
    product_type: str,
    time_of_use: str,
) -> UserProduct:
    product = UserProduct(
        user_id=user_id,
        product_name=product_name,
        product_type=product_type,
        time_of_use=time_of_use,
        status="active",
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def remove_user_product(session: AsyncSession, product_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(UserProduct).where(
            and_(UserProduct.id == product_id, UserProduct.user_id == user_id)
        )
    )
    product = result.scalar_one_or_none()
    if product:
        product.status = "removed"
        product.removed_at = datetime.utcnow()
        await session.commit()
        return True
    return False


# ── Reminders ────────────────────────────────────────────────────────────────

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
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def get_all_active_reminders(session: AsyncSession) -> list[Reminder]:
    result = await session.execute(
        select(Reminder).where(Reminder.active == True)
    )
    return result.scalars().all()


# ── Products catalog ──────────────────────────────────────────────────────────

async def search_catalog(session: AsyncSession, query: str) -> list[ProductCatalog]:
    result = await session.execute(
        select(ProductCatalog).where(
            ProductCatalog.name.ilike(f"%{query}%")
        ).limit(5)
    )
    return result.scalars().all()


async def get_catalog_product(session: AsyncSession, product_id: int) -> Optional[ProductCatalog]:
    result = await session.execute(
        select(ProductCatalog).where(ProductCatalog.id == product_id)
    )
    return result.scalar_one_or_none()


async def add_catalog_product(
    session: AsyncSession,
    name: str,
    brand: Optional[str],
    category: str,
    ingredients_raw: str,
    ingredients_parsed: list,
    source: str = "user_ocr",
    verified: bool = False,
) -> ProductCatalog:
    product = ProductCatalog(
        name=name,
        brand=brand,
        category=category,
        ingredients_raw=ingredients_raw,
        ingredients_parsed=ingredients_parsed,
        source=source,
        verified=verified,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def increment_scan_count(session: AsyncSession, product_id: int) -> None:
    result = await session.execute(
        select(ProductCatalog).where(ProductCatalog.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product:
        product.scan_count = (product.scan_count or 0) + 1
        await session.commit()


# ── Ingredients library ───────────────────────────────────────────────────────

async def get_ingredient_by_inci(
    session: AsyncSession, inci_name: str
) -> Optional[IngredientsLibrary]:
    result = await session.execute(
        select(IngredientsLibrary).where(
            IngredientsLibrary.inci_name.ilike(inci_name)
        )
    )
    return result.scalar_one_or_none()


async def get_ingredients_bulk(
    session: AsyncSession, inci_names: list[str]
) -> list[IngredientsLibrary]:
    result = await session.execute(
        select(IngredientsLibrary).where(
            IngredientsLibrary.inci_name.in_(inci_names)
        )
    )
    return result.scalars().all()


# ── Product scans ─────────────────────────────────────────────────────────────

async def save_product_scan(
    session: AsyncSession,
    user_id: int,
    product_name: str,
    ingredients_raw: str,
    ingredients_parsed: list,
    score: int,
    suitable: bool,
    warnings: list,
    product_id: Optional[int] = None,
) -> ProductScan:
    scan = ProductScan(
        user_id=user_id,
        product_id=product_id,
        product_name=product_name,
        ingredients_raw=ingredients_raw,
        ingredients_parsed=ingredients_parsed,
        score=score,
        suitable=suitable,
        warnings=warnings,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    return scan


async def get_user_scans(session: AsyncSession, user_id: int) -> list[ProductScan]:
    result = await session.execute(
        select(ProductScan)
        .where(ProductScan.user_id == user_id)
        .order_by(ProductScan.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()
