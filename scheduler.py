"""APScheduler-based: напоминания + плановое обновление рутины."""
import logging
from datetime import datetime, date, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from database import async_session_factory
from database.queries import (
    get_all_active_reminders,
    get_today_tracking,
    get_latest_routine,
    grant_achievement,
)
from utils.keyboards import reminder_done_keyboard

logger = logging.getLogger(__name__)

ROUTINE_REFRESH_DAYS = 28  # предлагать обновление раз в 4 недели


async def check_and_send_reminders(bot: Bot) -> None:
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
            if (now_local.hour == reminder.morning_time.hour
                    and now_local.minute == reminder.morning_time.minute):
                async with async_session_factory() as session:
                    tracking = await get_today_tracking(session, reminder.user_id)
                if not (tracking and tracking.morning_done):
                    await _send_reminder(bot, reminder.user_id, "morning")

        if reminder.evening_time:
            if (now_local.hour == reminder.evening_time.hour
                    and now_local.minute == reminder.evening_time.minute):
                async with async_session_factory() as session:
                    tracking = await get_today_tracking(session, reminder.user_id)
                if not (tracking and tracking.evening_done):
                    await _send_reminder(bot, reminder.user_id, "evening")


async def check_routine_refresh(bot: Bot) -> None:
    """Раз в день проверяем — не пора ли предложить обновить рутину."""
    async with async_session_factory() as session:
        reminders = await get_all_active_reminders(session)

    today = date.today()
    for reminder in reminders:
        try:
            async with async_session_factory() as session:
                routine = await get_latest_routine(session, reminder.user_id)
            if not routine:
                continue
            routine_age = (today - routine.created_at.date()).days
            if routine_age >= ROUTINE_REFRESH_DAYS:
                await _send_routine_refresh(bot, reminder.user_id, routine_age)
        except Exception as e:
            logger.warning(f"Routine refresh check error for {reminder.user_id}: {e}")


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
    except Exception as e:
        logger.warning(f"Failed to send reminder to {user_id}: {e}")


async def _send_routine_refresh(bot: Bot, user_id: int, days_old: int) -> None:
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"✨ *Пора обновить рутину!*\n\n"
                f"Твоя рутина актуальна уже {days_old} дней.\n"
                "Кожа привыкает к одним и тем же продуктам — "
                "самое время скорректировать уход.\n\n"
                "Хочешь, чтобы AI обновил рутину с учётом изменений?\n"
                "Напиши /start и выбери «Обновить профиль»"
            ),
            parse_mode="Markdown",
        )
        logger.info(f"Sent routine refresh nudge to {user_id}")
    except Exception as e:
        logger.warning(f"Failed to send routine refresh to {user_id}: {e}")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Напоминания — каждую минуту
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="reminders",
        replace_existing=True,
    )

    # Проверка обновления рутины — раз в день в 10:00 UTC
    scheduler.add_job(
        check_routine_refresh,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        id="routine_refresh",
        replace_existing=True,
    )

    return scheduler
