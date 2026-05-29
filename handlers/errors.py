"""Shared Telegram error handling."""
import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

GENERIC_ERROR_TEXT = (
    "Что-то пошло не так. Попробуй ещё раз или вернись в главное меню через /start."
)


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log unhandled handler errors and give the user a short recovery path."""
    error = context.error
    exc_info = (
        (type(error), error, error.__traceback__)
        if isinstance(error, BaseException)
        else None
    )
    logger.error("Unhandled update error", exc_info=exc_info)

    if not isinstance(update, Update):
        return

    query = update.callback_query
    if query:
        try:
            await query.answer(GENERIC_ERROR_TEXT, show_alert=True)
            return
        except TelegramError:
            logger.debug("Could not answer callback query after error", exc_info=True)

    message = update.effective_message
    if message:
        try:
            await message.reply_text(GENERIC_ERROR_TEXT)
        except TelegramError:
            logger.debug("Could not notify user after error", exc_info=True)
