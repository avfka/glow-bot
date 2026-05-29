"""Leaderboard handler — Duolingo-стиль: лиги, стрики, достижения."""
import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from database import async_session_factory
from database.repositories.gamification import (
    ACHIEVEMENT_META,
    LEAGUE_CONFIG,
    get_leaderboard,
    get_user_achievements,
    next_league,
    streak_to_league,
)
from database.repositories.tracking import get_current_streak
from utils.keyboards import achievements_keyboard, leaderboard_keyboard

logger = logging.getLogger(__name__)

LEAGUE_EMOJIS = {
    "bronze": "🥉", "silver": "🥈", "gold": "🥇",
    "platinum": "🏆", "diamond": "💎",
}

ALL_ACHIEVEMENTS = list(ACHIEVEMENT_META.keys())


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    async with async_session_factory() as session:
        streak = await get_current_streak(session, user_id)
        board = await get_leaderboard(session, [user_id])

    league_code, league_label = streak_to_league(streak)
    league_emoji = LEAGUE_EMOJIS.get(league_code, "🥉")
    next_l = next_league(league_code)

    # League progress
    progress_text = ""
    if next_l:
        next_code, next_label, next_min = next_l
        days_left = max(0, next_min - streak)
        next_emoji = LEAGUE_EMOJIS.get(next_code, "")
        progress_text = f"До {next_emoji} {next_label}: ещё {days_left} дн.\n"

    # Leaderboard table
    medals = ["🥇", "🥈", "🥉"]
    board_lines = []
    for i, entry in enumerate(board[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        me = " ← ты" if entry["user_id"] == user_id else ""
        board_lines.append(f"{medal} *{entry['name']}* — {entry['weekly_days']} дн. {me}")

    board_text = "\n".join(board_lines) if board_lines else "_Пока только ты_"

    if len(board) == 1:
        invite_hint = "\n\n💡 _Пригласи подругу — соревнуйтесь вместе!_"
    else:
        invite_hint = ""

    text = (
        f"🏆 *Лидерборд*\n\n"
        f"Твоя лига: {league_emoji} *{league_label}*\n"
        f"Стрик: 🔥 {streak} дн.\n"
        f"{progress_text}\n"
        f"📊 *Топ недели:*\n{board_text}"
        f"{invite_hint}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=leaderboard_keyboard(referral_link),
    )


async def btn_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    async with async_session_factory() as session:
        earned = await get_user_achievements(session, user_id)

    lines = ["🏅 *Мои достижения*\n"]
    for code, (emoji, title, desc) in ACHIEVEMENT_META.items():
        if code in earned:
            lines.append(f"✅ {emoji} *{title}*\n   _{desc}_")
        else:
            lines.append(f"⬜ {emoji} {title}\n   _{desc}_")
        lines.append("")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=achievements_keyboard(),
    )


async def btn_back_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Вернись в лидерборд через меню 👇")


def get_leaderboard_handlers() -> list:
    return [
        CommandHandler("leaderboard", cmd_leaderboard),
        MessageHandler(filters.Regex("^🏆 Лидерборд$"), cmd_leaderboard),
        CallbackQueryHandler(btn_achievements, pattern="^league:achievements$"),
        CallbackQueryHandler(btn_back_leaderboard, pattern="^league:back$"),
    ]
