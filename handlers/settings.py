"""Settings handler: reminders, profile update."""
import logging
from datetime import time

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database import async_session_factory
from database.repositories.reminders import get_reminder, upsert_reminder
from utils.keyboards import settings_keyboard, start_onboarding_keyboard, timezone_keyboard

logger = logging.getLogger(__name__)

WAIT_SETTINGS_ACTION = 0
WAIT_MORNING_REMINDER, WAIT_EVENING_REMINDER, WAIT_REMINDER_TZ = range(1, 4)


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        reminder = await get_reminder(session, user_id)

    if reminder:
        morning = reminder.morning_time.strftime("%H:%M") if reminder.morning_time else "не задано"
        evening = reminder.evening_time.strftime("%H:%M") if reminder.evening_time else "не задано"
        tz = reminder.timezone or "Europe/Moscow"
        reminder_text = f"\n\n⏰ *Напоминания:*\nУтро: {morning}\nВечер: {evening}\nЧасовой пояс: {tz}"
    else:
        reminder_text = "\n\n⏰ *Напоминания:* не настроены"

    await update.message.reply_text(
        f"⚙️ *Настройки*{reminder_text}",
        parse_mode="Markdown",
        reply_markup=settings_keyboard(),
    )


async def btn_settings_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⏰ *Изменить напоминания*\n\n"
        "Введи время утреннего напоминания (ЧЧ:ММ)\n"
        "или /skip чтобы пропустить:",
        parse_mode="Markdown",
    )
    return WAIT_MORNING_REMINDER


async def btn_settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👤 Чтобы обновить профиль кожи, запусти новый анализ.",
        reply_markup=start_onboarding_keyboard(),
    )


async def receive_morning_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not _validate_time(text):
        await update.message.reply_text("Неверный формат. Используй ЧЧ:ММ, например 08:00")
        return WAIT_MORNING_REMINDER

    context.user_data["new_reminder"] = {"morning": text}
    await update.message.reply_text(
        "🌙 Введи время вечернего напоминания (ЧЧ:ММ)\n"
        "или /skip чтобы пропустить:"
    )
    return WAIT_EVENING_REMINDER


async def skip_morning_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_reminder"] = {"morning": None}
    await update.message.reply_text(
        "🌙 Введи время вечернего напоминания (ЧЧ:ММ)\n"
        "или /skip чтобы пропустить:"
    )
    return WAIT_EVENING_REMINDER


async def receive_evening_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not _validate_time(text):
        await update.message.reply_text("Неверный формат. Используй ЧЧ:ММ, например 21:00")
        return WAIT_EVENING_REMINDER

    reminder_data = context.user_data.get("new_reminder")
    if reminder_data is None:
        await update.message.reply_text(
            "Сессия настройки устарела. Открой /settings и начни заново."
        )
        return ConversationHandler.END

    reminder_data["evening"] = text
    await update.message.reply_text("🌍 Выбери часовой пояс:", reply_markup=timezone_keyboard())
    return WAIT_REMINDER_TZ


async def skip_evening_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reminder_data = context.user_data.get("new_reminder")
    if reminder_data is None:
        await update.message.reply_text(
            "Сессия настройки устарела. Открой /settings и начни заново."
        )
        return ConversationHandler.END

    reminder_data["evening"] = None
    await update.message.reply_text("🌍 Выбери часовой пояс:", reply_markup=timezone_keyboard())
    return WAIT_REMINDER_TZ


async def choose_reminder_tz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tz = query.data.split(":", 1)[1]
    user_id = query.from_user.id
    reminder_data = context.user_data.pop("new_reminder", None)
    if reminder_data is None:
        await query.edit_message_text(
            "Сессия настройки устарела. Открой /settings и начни заново."
        )
        return ConversationHandler.END

    morning_time = _parse_time(reminder_data.get("morning"))
    evening_time = _parse_time(reminder_data.get("evening"))

    async with async_session_factory() as session:
        await upsert_reminder(
            session=session,
            user_id=user_id,
            morning_time=morning_time,
            evening_time=evening_time,
            timezone=tz,
            active=True,
            commit=False,
        )
        await session.commit()

    morning_str = morning_time.strftime("%H:%M") if morning_time else "не задано"
    evening_str = evening_time.strftime("%H:%M") if evening_time else "не задано"

    await query.edit_message_text(
        f"✅ *Напоминания сохранены!*\n\n"
        f"🌅 Утро: {morning_str}\n"
        f"🌙 Вечер: {evening_str}\n"
        f"🌍 Часовой пояс: {tz}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def _validate_time(text: str) -> bool:
    try:
        parts = text.split(":")
        if len(parts) != 2:
            return False
        return 0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59
    except Exception:
        return False


def _parse_time(text) -> time | None:
    if not text:
        return None
    try:
        parts = text.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return None


async def cancel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_reminder", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Настройка отменена.")
    else:
        await update.message.reply_text("Настройка отменена.")
    return ConversationHandler.END


def get_settings_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(btn_settings_reminders, pattern="^settings:reminders$"),
        ],
        states={
            WAIT_MORNING_REMINDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_morning_reminder),
                CommandHandler("skip", skip_morning_reminder),
            ],
            WAIT_EVENING_REMINDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_evening_reminder),
                CommandHandler("skip", skip_evening_reminder),
            ],
            WAIT_REMINDER_TZ: [
                CallbackQueryHandler(choose_reminder_tz, pattern="^tz:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_settings),
            CallbackQueryHandler(cancel_settings, pattern="^cancel:settings$"),
        ],
        per_message=False,
    )


def get_settings_handlers() -> list:
    return [
        CommandHandler("settings", cmd_settings),
        MessageHandler(filters.Regex("^⚙️ Настройки$"), cmd_settings),
        CallbackQueryHandler(btn_settings_profile, pattern="^settings:profile$"),
        get_settings_handler(),
    ]
