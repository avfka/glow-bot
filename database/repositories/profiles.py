from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import SkinAnalysisHistory, UserProfileVersion
from database.repositories.common import finish_write, persist


async def get_latest_profile(
    session: AsyncSession, user_id: int
) -> Optional[UserProfileVersion]:
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
    *,
    commit: bool = True,
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
    return await persist(session, profile, commit)


async def save_skin_analysis(
    session: AsyncSession,
    user_id: int,
    photo_path: Optional[str],
    ai_raw_response: dict,
    ai_detected_problems: list,
    user_confirmed_problems: Optional[list] = None,
    user_corrections: bool = False,
    skin_score: Optional[dict] = None,
    *,
    commit: bool = True,
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
    return await persist(session, record, commit)


async def update_analysis_user_confirmation(
    session: AsyncSession,
    analysis_id: int,
    user_confirmed_problems: list,
    user_corrections: bool,
    *,
    commit: bool = True,
) -> None:
    result = await session.execute(
        select(SkinAnalysisHistory).where(SkinAnalysisHistory.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis:
        analysis.user_confirmed_problems = user_confirmed_problems
        analysis.user_corrections = user_corrections
        await finish_write(session, commit)
