"""Friends and leaderboard handler."""
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
from database.repositories.tracking import get_streak_leaderboard
from utils.keyboards import friends_keyboard

logger = logging.getLogger(__name__)


async def cmd_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    await update.message.reply_text(
        "👯 *Соревнование с друзьями*\n\n"
        "Пригласи друзей и соревнуйтесь в стриках!\n\n"
        "📤 Твоя реферальная ссылка:\n"
        f"`{referral_link}`\n\n"
        "Поделись ею с подругами — и следи за общим рейтингом 🔥",
        parse_mode="Markdown",
        reply_markup=friends_keyboard(referral_link),
    )


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # TODO: fetch actual friends list from a friends table (future feature)
    # For now just show the current user's rank
    async with async_session_factory() as session:
        board = await get_streak_leaderboard(session, [user_id])

    lines = ["🏆 *Таблица лидеров*\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, entry in enumerate(board):
        medal = medals[i] if i < 3 else f"{i + 1}."
        streak = entry["streak"]
        name = entry["name"]
        mark = " ← ты" if entry["user_id"] == user_id else ""
        lines.append(f"{medal} *{name}* — {streak} дн.{mark}")

    if len(board) == 1:
        lines.append("\n_Пригласи друзей чтобы увидеть рейтинг_ /friends")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


def get_friends_handlers() -> list:
    return [
        CommandHandler("friends", cmd_friends),
        CommandHandler("leaderboard", cmd_leaderboard),
        MessageHandler(filters.Regex("^👯 Друзья$"), cmd_friends),
    ]
