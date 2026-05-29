"""Tracking handler: mark routines done, show streak."""
import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import async_session_factory
from database.repositories.gamification import ACHIEVEMENT_META
from database.repositories.tracking import get_current_streak, get_today_tracking
from services.tracking import apply_tracking_toggle, save_tracking_status
from utils.keyboards import tracking_keyboard

logger = logging.getLogger(__name__)


async def cmd_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        tracking = await get_today_tracking(session, user_id)

    morning_done = tracking.morning_done if tracking else False
    evening_done = tracking.evening_done if tracking else False

    await update.message.reply_text(
        "✅ *Отметь выполнение рутины на сегодня:*\n\n"
        "Выбери утро и/или вечер, затем нажми *Сохранить отметку*.",
        parse_mode="Markdown",
        reply_markup=tracking_keyboard(morning_done, evening_done),
    )


async def btn_track_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.split(":")[1]

    if action == "save":
        await _save_tracking(query, context)
        return

    pending = context.user_data.get("pending_track")
    if pending is not None:
        morning_done = pending["morning_done"]
        evening_done = pending["evening_done"]
    else:
        async with async_session_factory() as session:
            tracking = await get_today_tracking(session, user_id)
        morning_done = tracking.morning_done if tracking else False
        evening_done = tracking.evening_done if tracking else False

    morning_done, evening_done = apply_tracking_toggle(
        action=action,
        morning_done=morning_done,
        evening_done=evening_done,
    )

    context.user_data["pending_track"] = {
        "morning_done": morning_done,
        "evening_done": evening_done,
    }

    await query.edit_message_reply_markup(
        reply_markup=tracking_keyboard(morning_done, evening_done)
    )


async def _save_tracking(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = query.from_user.id
    pending = context.user_data.pop("pending_track", None)

    if pending is None:
        async with async_session_factory() as session:
            tracking = await get_today_tracking(session, user_id)
        if tracking:
            pending = {
                "morning_done": tracking.morning_done,
                "evening_done": tracking.evening_done,
            }
        else:
            pending = {"morning_done": False, "evening_done": False}

    morning_done = pending["morning_done"]
    evening_done = pending["evening_done"]

    async with async_session_factory() as session:
        result = await save_tracking_status(
            session,
            user_id=user_id,
            morning_done=morning_done,
            evening_done=evening_done,
        )

    done_parts = []
    if morning_done:
        done_parts.append("🌅 утренняя")
    if evening_done:
        done_parts.append("🌙 вечерняя")

    if done_parts:
        done_text = " и ".join(done_parts) + " рутина выполнена!"
    else:
        done_text = "Ничего не отмечено."

    streak_text = ""
    if morning_done and evening_done:
        streak_text = f"\n\n🔥 *Стрик: {result.streak} {'день' if result.streak == 1 else 'дней'}!*"
        if result.streak >= 7:
            streak_text += "\n🏆 Целая неделя — ты молодец!"
        elif result.streak >= 3:
            streak_text += "\n✨ Отличная серия!"

    ach_text = ""
    for code in result.new_achievements:
        meta = ACHIEVEMENT_META.get(code)
        if meta:
            ach_text += f"\n🎉 Новое достижение: *{meta[0]} {meta[1]}*"

    await query.edit_message_text(
        f"💾 Сохранено!\n\n{done_text}{streak_text}{ach_text}",
        parse_mode="Markdown",
    )


async def quick_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick tracking from reminder push."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    period = query.data.split(":")[1]

    async with async_session_factory() as session:
        tracking = await get_today_tracking(session, user_id)
        morning_done = tracking.morning_done if tracking else False
        evening_done = tracking.evening_done if tracking else False

        if period == "morning":
            morning_done = True
        elif period == "evening":
            evening_done = True

        result = await save_tracking_status(
            session,
            user_id=user_id,
            morning_done=morning_done,
            evening_done=evening_done,
        )

    label = "утренняя" if period == "morning" else "вечерняя"
    await query.edit_message_text(
        f"✅ {label.capitalize()} рутина отмечена!\n🔥 Стрик: {result.streak} дн."
    )


async def cmd_streak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        streak = await get_current_streak(session, user_id)
        tracking = await get_today_tracking(session, user_id)

    morning_done = tracking.morning_done if tracking else False
    evening_done = tracking.evening_done if tracking else False

    status_parts = []
    if morning_done:
        status_parts.append("✅ Утренняя рутина")
    else:
        status_parts.append("☐ Утренняя рутина")
    if evening_done:
        status_parts.append("✅ Вечерняя рутина")
    else:
        status_parts.append("☐ Вечерняя рутина")

    status_text = "\n".join(status_parts)

    if streak == 0:
        streak_emoji = "💤"
        streak_msg = "Начни сегодня — отметь рутину!"
    elif streak < 3:
        streak_emoji = "🌱"
        streak_msg = "Отличное начало!"
    elif streak < 7:
        streak_emoji = "🔥"
        streak_msg = "Ты в ударе!"
    elif streak < 14:
        streak_emoji = "🔥🔥"
        streak_msg = "Неделя! Продолжай!"
    else:
        streak_emoji = "🏆"
        streak_msg = "Легенда ухода за кожей!"

    await update.message.reply_text(
        f"{streak_emoji} *Твой стрик: {streak} {'день' if streak == 1 else 'дней'}*\n\n"
        f"{streak_msg}\n\n"
        f"*Сегодня:*\n{status_text}",
        parse_mode="Markdown",
    )


def get_tracking_handlers() -> list:
    return [
        CommandHandler("track", cmd_track),
        CommandHandler("streak", cmd_streak),
        MessageHandler(filters.Regex("^✅ Отметить выполнение$"), cmd_track),
        MessageHandler(filters.Regex("^🔥 Мой стрик$"), cmd_streak),
        CallbackQueryHandler(btn_track_toggle, pattern="^track:"),
        CallbackQueryHandler(quick_track, pattern="^quick_track:"),
    ]
