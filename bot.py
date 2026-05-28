"""GlowBot — AI-косметолог. Entry point."""
import logging
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from database import init_db
from handlers.onboarding import get_onboarding_handler
from handlers.routine import get_routine_handlers
from handlers.profile import get_profile_handlers
from handlers.product_search import get_product_search_handler
from handlers.leaderboard import get_leaderboard_handlers
from handlers.products import get_products_handlers
from handlers.scanner import get_scanner_handler
from handlers.settings import get_settings_handlers
from scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


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

    # Onboarding — первым (handles /start)
    app.add_handler(get_onboarding_handler())

    # Profile
    for h in get_profile_handlers():
        app.add_handler(h)

    # Routine (step-by-step + tracking)
    for h in get_routine_handlers():
        app.add_handler(h)

    # Product search (AI recommendations)
    app.add_handler(get_product_search_handler())

    # Leaderboard (Duolingo-style)
    for h in get_leaderboard_handlers():
        app.add_handler(h)

    # Products management
    for h in get_products_handlers():
        app.add_handler(h)

    # Scanner
    app.add_handler(get_scanner_handler())

    # Settings
    for h in get_settings_handlers():
        app.add_handler(h)

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
