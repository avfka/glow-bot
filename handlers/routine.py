"""Routine handler — пошаговая рутина с привязкой продуктов."""
import logging

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
from database.repositories.routines import (
    get_latest_routine,
    get_routine_products,
    set_routine_product,
)
from database.repositories.tracking import get_today_tracking
from utils.keyboards import (
    main_menu_keyboard,
    routine_period_keyboard,
    routine_steps_keyboard,
    start_onboarding_keyboard,
    tracking_keyboard,
)

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "⚠️ _Анализ носит рекомендательный характер и не является "
    "медицинским заключением. При серьёзных проблемах кожи "
    "обратитесь к дерматологу._"
)

WAIT_PRODUCT_NAME = 0

STEP_ICONS = {
    "cleanser": "🧼", "toner": "💦", "serum": "💉",
    "moisturizer": "🥛", "spf": "☀️", "eye_care": "👁",
    "mask": "🌿", "other": "📦",
}


def _format_routine_with_products(steps: list, period: str, step_products: dict) -> str:
    if not steps:
        return "_Рутина пока не заполнена_"
    lines = []
    for i, step in enumerate(steps):
        ptype = step.get("product_type", "other")
        icon = STEP_ICONS.get(ptype, "📦")
        name = step.get("name", f"Шаг {i+1}")
        desc = step.get("description", "")
        product = step_products.get(f"{period}_{i}", "")

        lines.append(f"{icon} *{i+1}. {name}*")
        if desc:
            lines.append(f"   _{desc}_")
        if product:
            lines.append(f"   ✅ _{product}_")
        else:
            lines.append(f"   ➕ _не выбран продукт_")
        lines.append("")
    return "\n".join(lines)


async def cmd_routine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        routine = await get_latest_routine(session, user_id)

    if not routine:
        await update.message.reply_text(
            "💆 У тебя пока нет рутины.\n\n"
            "Сначала создай профиль кожи — после анализа я составлю утренний и вечерний уход.",
            reply_markup=start_onboarding_keyboard(),
        )
        return

    await update.message.reply_text(
        "💆 *Моя рутина*\n\nВыбери что хочешь посмотреть:",
        parse_mode="Markdown",
        reply_markup=routine_period_keyboard(),
    )


async def btn_show_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    period = query.data.split(":")[1]
    user_id = query.from_user.id

    async with async_session_factory() as session:
        routine = await get_latest_routine(session, user_id)
        step_products = await get_routine_products(session, user_id)

    if not routine:
        await query.edit_message_text(
            "Рутина не найдена. Сначала создай профиль кожи.",
            reply_markup=start_onboarding_keyboard(),
        )
        return

    if period == "morning":
        steps = routine.morning_steps or []
        title = "🌅 *Утренняя рутина*"
    else:
        steps = routine.evening_steps or []
        title = "🌙 *Вечерняя рутина*"

    steps_text = _format_routine_with_products(steps, period, step_products)

    await query.edit_message_text(
        f"{title}\n\n{steps_text}\n{DISCLAIMER}\n\n"
        "Нажми на шаг чтобы привязать свой продукт:",
        parse_mode="Markdown",
        reply_markup=routine_steps_keyboard(steps, period, step_products),
    )


async def btn_assign_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, period, step_idx = query.data.split(":")
    context.user_data["assign"] = {"period": period, "step_index": int(step_idx)}

    async with async_session_factory() as session:
        routine = await get_latest_routine(session, query.from_user.id)

    steps = (routine.morning_steps if period == "morning" else routine.evening_steps) or []
    idx = int(step_idx)
    step_name = steps[idx].get("name", f"Шаг {idx+1}") if idx < len(steps) else f"Шаг {idx+1}"

    await query.edit_message_text(
        f"💬 Напиши название продукта для *{step_name}*\n\n"
        "_Например: La Roche-Posay Effaclar_\n\n"
        "Или /skip чтобы убрать продукт с этого шага",
        parse_mode="Markdown",
    )
    return WAIT_PRODUCT_NAME


async def receive_product_for_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    assign = context.user_data.pop("assign", None)
    if not assign:
        await update.message.reply_text("Что-то пошло не так. Попробуй снова.")
        return ConversationHandler.END

    product_name = update.message.text.strip()
    async with async_session_factory() as session:
        await set_routine_product(
            session=session,
            user_id=user_id,
            period=assign["period"],
            step_index=assign["step_index"],
            product_name=product_name,
            commit=False,
        )
        await session.commit()

    period_ru = "утренней" if assign["period"] == "morning" else "вечерней"
    await update.message.reply_text(
        f"✅ Продукт *{product_name}* добавлен в {period_ru} рутину!",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def skip_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    assign = context.user_data.pop("assign", None)
    if assign:
        async with async_session_factory() as session:
            await set_routine_product(
                session=session,
                user_id=update.effective_user.id,
                period=assign["period"],
                step_index=assign["step_index"],
                product_name="",
                commit=False,
            )
            await session.commit()
    await update.message.reply_text("Продукт убран с шага.")
    return ConversationHandler.END


async def btn_track_from_routine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    async with async_session_factory() as session:
        tracking = await get_today_tracking(session, user_id)

    morning_done = tracking.morning_done if tracking else False
    evening_done = tracking.evening_done if tracking else False

    await query.edit_message_text(
        "✅ *Отметь выполнение рутины на сегодня:*\n\n"
        "Выбери утро и/или вечер, затем нажми *Сохранить отметку*.",
        parse_mode="Markdown",
        reply_markup=tracking_keyboard(morning_done, evening_done),
    )


def get_routine_assign_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(btn_assign_product, pattern="^assign_product:"),
        ],
        states={
            WAIT_PRODUCT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_for_step),
                CommandHandler("skip", skip_assign),
            ],
        },
        fallbacks=[CommandHandler("cancel", skip_assign)],
        per_message=False,
    )


def get_routine_handlers() -> list:
    return [
        CommandHandler("routine", cmd_routine),
        MessageHandler(filters.Regex("^💆 Моя рутина$"), cmd_routine),
        CallbackQueryHandler(btn_show_period, pattern="^routine:(morning|evening)$"),
        CallbackQueryHandler(btn_track_from_routine, pattern="^routine:track$"),
        get_routine_assign_handler(),
    ]
