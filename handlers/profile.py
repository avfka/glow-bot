"""Profile handler — просмотр и обновление профиля кожи."""
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from database import async_session_factory
from database.queries import (
    ACHIEVEMENT_META,
    get_current_streak,
    get_latest_profile,
    get_today_tracking,
    get_user,
    get_user_achievements,
    get_active_products,
)
from utils.keyboards import profile_keyboard

logger = logging.getLogger(__name__)

SKIN_TYPE_RU = {
    "oily": "Жирная",
    "dry": "Сухая",
    "combination": "Комбинированная",
    "sensitive": "Чувствительная",
}

PROBLEMS_RU = {
    "acne": "Акне", "rosacea": "Розацеа", "couperose": "Купероз",
    "pigmentation": "Пигментация", "wrinkles": "Морщины", "redness": "Покраснения",
    "enlarged_pores": "Расш. поры", "dryness": "Сухость", "oiliness": "Жирный блеск",
    "eczema": "Экзема", "psoriasis": "Псориаз", "sensitivity": "Чувствительность",
    "puffiness": "Отёчность",
}

BUDGET_RU = {"low": "Бюджетный", "medium": "Средний", "high": "Премиум"}
GOAL_RU = {"hydration": "Увлажнение", "tone": "Выравнивание тона", "anti-age": "Антивозрастной"}


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    async with async_session_factory() as session:
        user = await get_user(session, user_id)
        profile = await get_latest_profile(session, user_id)
        streak = await get_current_streak(session, user_id)
        tracking = await get_today_tracking(session, user_id)
        products = await get_active_products(session, user_id)
        achievements = await get_user_achievements(session, user_id)

    if not profile:
        await update.message.reply_text(
            "👤 Профиль ещё не создан.\n\nПройди анализ кожи → /start"
        )
        return

    # Problems
    problems = profile.skin_problems or []
    problems_text = ", ".join(PROBLEMS_RU.get(p, p) for p in problems) if problems else "не указаны"

    # Today's status
    morning_done = tracking.morning_done if tracking else False
    evening_done = tracking.evening_done if tracking else False
    today_status = []
    today_status.append("✅ утро" if morning_done else "☐ утро")
    today_status.append("✅ вечер" if evening_done else "☐ вечер")

    # Achievements preview (last 3)
    ach_text = ""
    if achievements:
        ach_lines = []
        for code in achievements[-3:]:
            meta = ACHIEVEMENT_META.get(code)
            if meta:
                ach_lines.append(f"{meta[0]} {meta[1]}")
        if ach_lines:
            ach_text = "\n\n🏅 *Достижения:*\n" + "\n".join(ach_lines)
        if len(achievements) > 3:
            ach_text += f"\n_и ещё {len(achievements) - 3}_"

    # Profile date
    date_str = profile.created_at.strftime("%d.%m.%Y") if profile.created_at else "—"

    text = (
        f"👤 *Мой профиль*\n\n"
        f"*Тип кожи:* {SKIN_TYPE_RU.get(profile.skin_type, profile.skin_type or '—')}\n"
        f"*Проблемы:* {problems_text}\n"
        f"*Цель:* {GOAL_RU.get(profile.goal or '', profile.goal or '—')}\n"
        f"*Бюджет:* {BUDGET_RU.get(profile.budget or '', profile.budget or '—')}\n"
        f"*Возраст:* {profile.age or '—'} лет\n"
        f"*Аллергии:* {profile.allergies or 'нет'}\n\n"
        f"📊 *Статистика:*\n"
        f"🔥 Стрик: {streak} дн.\n"
        f"🧴 Продуктов: {len(products)}\n"
        f"📅 Сегодня: {' | '.join(today_status)}\n"
        f"\n_Профиль обновлён: {date_str}_"
        f"{ach_text}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=profile_keyboard(),
    )


async def btn_profile_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Чтобы обновить профиль кожи, пройди новый анализ.\n\n"
        "Напиши /start — бот предложит обновить данные.",
    )


def get_profile_handlers() -> list:
    return [
        CommandHandler("profile", cmd_profile),
        MessageHandler(filters.Regex("^👤 Профиль$"), cmd_profile),
        CallbackQueryHandler(btn_profile_update, pattern="^profile:update$"),
    ]
