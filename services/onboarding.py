"""Onboarding workflow use cases."""
from dataclasses import dataclass
from datetime import time
from typing import Optional

from services import get_analyzer
from services.skin_analyzer import SkinAnalysisResult


@dataclass
class OnboardingCompletionResult:
    routine_result: SkinAnalysisResult


async def complete_onboarding(
    *,
    user_id: int,
    onboarding_data: dict,
    confirmed_problems: list,
    user_corrections: bool,
) -> OnboardingCompletionResult:
    from database import async_session_factory
    from database.repositories.profiles import (
        create_profile_version,
        update_analysis_user_confirmation,
    )
    from database.repositories.reminders import upsert_reminder
    from database.repositories.routines import (
        create_routine,
    )

    async with async_session_factory() as session:
        analysis_id = onboarding_data.get("analysis_id")
        if analysis_id:
            await update_analysis_user_confirmation(
                session,
                analysis_id,
                confirmed_problems,
                user_corrections,
                commit=False,
            )

        profile = await create_profile_version(
            session=session,
            user_id=user_id,
            skin_type=onboarding_data.get("skin_type", "combination"),
            skin_problems=confirmed_problems,
            allergies=onboarding_data.get("allergies"),
            budget=onboarding_data.get("budget", "medium"),
            goal=onboarding_data.get("goal", "hydration"),
            age=onboarding_data.get("age", 25),
            changed_by="user" if user_corrections else "ai",
            change_reason="Онбординг",
            commit=False,
        )
        await session.commit()

    analyzer = get_analyzer()
    routine_result = await analyzer.generate_routine(
        profile={
            "skin_type": profile.skin_type,
            "skin_problems": confirmed_problems,
            "allergies": profile.allergies,
            "budget": profile.budget,
            "goal": profile.goal,
            "age": profile.age,
        },
        user_products=[],
    )

    async with async_session_factory() as session:
        await create_routine(
            session=session,
            user_id=user_id,
            morning_steps=routine_result.morning_routine,
            evening_steps=routine_result.evening_routine,
            reason_for_change="Первичный анализ",
            commit=False,
        )

        morning_time = parse_time(onboarding_data.get("morning_time"))
        evening_time = parse_time(onboarding_data.get("evening_time"))
        if morning_time or evening_time:
            await upsert_reminder(
                session=session,
                user_id=user_id,
                morning_time=morning_time,
                evening_time=evening_time,
                timezone=onboarding_data.get("timezone", "Europe/Moscow"),
                commit=False,
            )
        await session.commit()

    return OnboardingCompletionResult(routine_result=routine_result)


def parse_time(time_str: Optional[str]) -> Optional[time]:
    if not time_str:
        return None
    try:
        hours, minutes = time_str.split(":")
        return time(int(hours), int(minutes))
    except Exception:
        return None
