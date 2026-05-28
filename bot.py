"""GlowBot — AI-косметолог. Entry point."""
import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import settings
from database import init_db
from handlers.onboarding import get_onboarding_handler
from handlers.tracking import get_tracking_handlers
from handlers.products import get_products_handlers
from handlers.scanner import get_scanner_handler
from handlers.friends import get_friends_handlers
from handlers.settings import get_settings_handlers
from scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

DISCLAIMER = (
    "⚠️ Анализ носит рекомендательный характер и не является "
    "медицинским заключением. При серьёзных проблемах кожи "
    "обратитесь к дерматологу."
)


async def cmd_routine(update: Update, context) -> None:
    from database import async_session_factory
    from database.queries import get_latest_routine

    user_id = update.effective_user.id
    async with async_session_factory() as session:
        routine = await get_latest_routine(session, user_id)

    if not routine:
        await update.message.reply_text(
            "У тебя пока нет рутины.\n"
            "Пройди анализ кожи → /start"
        )
        return

    def fmt(steps):
        if not steps:
            return "• Нет шагов"
        lines = []
        for step in steps:
            lines.append(f"{step.get('step', '•')}. *{step.get('name', '')}*")
            if step.get("description"):
                lines.append(f"   _{step['description']}_")
        return "\n".join(lines)

    period = context.args[0] if context.args else None
    if period == "morning":
        text = f"🌅 *Утренняя рутина:*\n\n{fmt(routine.morning_steps)}"
    elif period == "evening":
        text = f"🌙 *Вечерняя рутина:*\n\n{fmt(routine.evening_steps)}"
    else:
        text = (
            f"🌅 *Утренняя рутина:*\n{fmt(routine.morning_steps)}\n\n"
            f"🌙 *Вечерняя рутина:*\n{fmt(routine.evening_steps)}"
        )

    text += f"\n\n_{DISCLAIMER}_"
    await update.message.reply_text(text, parse_mode="Markdown")


async def morning_routine(update: Update, context) -> None:
    context.args = ["morning"]
    await cmd_routine(update, context)


async def evening_routine(update: Update, context) -> None:
    context.args = ["evening"]
    await cmd_routine(update, context)


async def post_init(application: Application) -> None:
    await init_db()
    logger.info("Database initialised")

    scheduler = create_scheduler(application.bot)
    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logger.info("Scheduler started")


async def post_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def main() -> None:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Onboarding (must be first — handles /start)
    app.add_handler(get_onboarding_handler())

    # Routine commands
    app.add_handler(CommandHandler("routine", cmd_routine))
    app.add_handler(MessageHandler(filters.Regex("^🌅 Утренняя рутина$"), morning_routine))
    app.add_handler(MessageHandler(filters.Regex("^🌙 Вечерняя рутина$"), evening_routine))

    # Tracking
    for handler in get_tracking_handlers():
        app.add_handler(handler)

    # Products
    for handler in get_products_handlers():
        app.add_handler(handler)

    # Scanner (conversation — before simple handlers)
    app.add_handler(get_scanner_handler())

    # Friends
    for handler in get_friends_handlers():
        app.add_handler(handler)

    # Settings
    for handler in get_settings_handlers():
        app.add_handler(handler)

    # Start bot
    if settings.webhook_url:
        logger.info(f"Starting webhook on port {settings.port}")
        app.run_webhook(
            listen="0.0.0.0",
            port=settings.port,
            webhook_url=settings.webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        logger.info("Starting polling")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
