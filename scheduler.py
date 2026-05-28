"""APScheduler-based reminder system."""
import logging
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from database import async_session_factory
from database.queries import get_all_active_reminders, get_today_tracking
from utils.keyboards import reminder_done_keyboard

logger = logging.getLogger(__name__)


async def check_and_send_reminders(bot: Bot) -> None:
    now_utc = datetime.utcnow().replace(second=0, microsecond=0)

    async with async_session_factory() as session:
        reminders = await get_all_active_reminders(session)

    for reminder in reminders:
        tz_name = reminder.timezone or "Europe/Moscow"
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.timezone("Europe/Moscow")

        now_local = datetime.now(tz).replace(second=0, microsecond=0)

        if reminder.morning_time:
            if (
                now_local.hour == reminder.morning_time.hour
                and now_local.minute == reminder.morning_time.minute
            ):
                async with async_session_factory() as session:
                    tracking = await get_today_tracking(session, reminder.user_id)
                if not (tracking and tracking.morning_done):
                    await _send_reminder(bot, reminder.user_id, "morning")

        if reminder.evening_time:
            if (
                now_local.hour == reminder.evening_time.hour
                and now_local.minute == reminder.evening_time.minute
            ):
                async with async_session_factory() as session:
                    tracking = await get_today_tracking(session, reminder.user_id)
                if not (tracking and tracking.evening_done):
                    await _send_reminder(bot, reminder.user_id, "evening")


async def _send_reminder(bot: Bot, user_id: int, period: str) -> None:
    if period == "morning":
        text = (
            "🌅 *Доброе утро!*\n\n"
            "Время для утренней рутины ухода за кожей ✨\n"
            "Не забудь выполнить все шаги!"
        )
    else:
        text = (
            "🌙 *Добрый вечер!*\n\n"
            "Время для вечерней рутины ухода за кожей 🌸\n"
            "Заверши день правильным уходом!"
        )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=reminder_done_keyboard(period),
        )
        logger.info(f"Sent {period} reminder to user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to send reminder to {user_id}: {e}")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="reminders",
        replace_existing=True,
    )
    return scheduler
