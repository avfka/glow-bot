"""Super-admin commands for operational support."""
import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config import settings
from database import async_session_factory
from database.repositories.profiles import create_profile_version, get_latest_profile
from database.repositories.users import get_user, get_user_admin_stats, list_recent_users
from utils.admin import is_super_admin

logger = logging.getLogger(__name__)

EDITABLE_PROFILE_FIELDS = {"skin_type", "budget", "goal", "age", "allergies", "skin_problems"}


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        await update.message.reply_text("Нет доступа.")
        return

    async with async_session_factory() as session:
        users = await list_recent_users(session, limit=20)

    lines = ["🛠 *Админ-панель*", "", f"Пользователей: показаны последние {len(users)}", ""]
    for user in users:
        created = user.created_at.strftime("%d.%m %H:%M") if user.created_at else "—"
        lines.append(f"• `{user.user_id}` — {user.name or 'без имени'} · {created}")
    lines.extend(
        [
            "",
            "Команды:",
            "`/admin_user USER_ID`",
            "`/admin_set_profile USER_ID field value`",
        ]
    )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_admin_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        await update.message.reply_text("Нет доступа.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /admin_user USER_ID")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER_ID должен быть числом.")
        return

    async with async_session_factory() as session:
        user = await get_user(session, user_id)
        profile = await get_latest_profile(session, user_id)
        stats = await get_user_admin_stats(session, user_id)

    if not user:
        await update.message.reply_text("Пользователь не найден.")
        return

    profile_text = "профиль не создан"
    if profile:
        profile_text = (
            f"type={profile.skin_type or '—'}, goal={profile.goal or '—'}, "
            f"budget={profile.budget or '—'}, age={profile.age or '—'}, "
            f"problems={', '.join(profile.skin_problems or []) or '—'}"
        )
    last_tracking = stats["last_tracking_date"].isoformat() if stats["last_tracking_date"] else "—"
    text = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{user.user_id}`\n"
        f"Имя: {user.name or '—'}\n"
        f"Создан: {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else '—'}\n\n"
        f"*Профиль:* {profile_text}\n\n"
        f"*Активность:*\n"
        f"Продуктов: {stats['products_count']}\n"
        f"Сканов: {stats['scans_count']}\n"
        f"Анализов кожи: {stats['analyses_count']}\n"
        f"Стрик: {stats['streak']}\n"
        f"Последний трекинг: {last_tracking}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_admin_set_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        await update.message.reply_text("Нет доступа.")
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Использование: /admin_set_profile USER_ID field value\n"
            f"Поля: {', '.join(sorted(EDITABLE_PROFILE_FIELDS))}"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER_ID должен быть числом.")
        return

    field = context.args[1]
    value = " ".join(context.args[2:]).strip()
    if field not in EDITABLE_PROFILE_FIELDS:
        await update.message.reply_text(f"Недоступное поле. Можно: {', '.join(sorted(EDITABLE_PROFILE_FIELDS))}")
        return

    async with async_session_factory() as session:
        user = await get_user(session, user_id)
        profile = await get_latest_profile(session, user_id)
        if not user or not profile:
            await update.message.reply_text("Нужен существующий пользователь с профилем.")
            return

        data = {
            "skin_type": profile.skin_type,
            "skin_problems": profile.skin_problems or [],
            "allergies": profile.allergies,
            "budget": profile.budget,
            "goal": profile.goal,
            "age": profile.age,
        }
        try:
            data[field] = _parse_profile_value(field, value)
        except ValueError:
            await update.message.reply_text("Некорректное значение поля.")
            return
        await create_profile_version(
            session,
            user_id=user_id,
            changed_by="admin",
            change_reason=f"admin edit by {update.effective_user.id}: {field}",
            commit=False,
            **data,
        )
        await session.commit()

    logger.info("Admin %s updated profile %s field %s", update.effective_user.id, user_id, field)
    await update.message.reply_text(f"Готово: `{user_id}` обновлен, поле `{field}`.", parse_mode="Markdown")


def _parse_profile_value(field: str, value: str):
    if field == "age":
        return int(value)
    if field == "skin_problems":
        return [item.strip() for item in value.split(",") if item.strip()]
    if value.lower() in {"none", "null", "нет", "-"}:
        return None
    return value


def _is_allowed(update: Update) -> bool:
    return is_super_admin(update.effective_user.id if update.effective_user else None, settings.super_admin_ids)


def get_admin_handlers() -> list:
    return [
        CommandHandler("admin", cmd_admin),
        CommandHandler("admin_user", cmd_admin_user),
        CommandHandler("admin_set_profile", cmd_admin_set_profile),
    ]
