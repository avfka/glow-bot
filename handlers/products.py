"""Products management handler."""
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
from database.queries import (
    add_user_product,
    get_active_products,
    get_latest_profile,
    get_latest_routine,
    remove_user_product,
    create_routine,
)
from services import get_analyzer
from utils.keyboards import (
    main_menu_keyboard,
    product_time_keyboard,
    product_type_keyboard,
    products_list_keyboard,
)

logger = logging.getLogger(__name__)

WAIT_PRODUCT_NAME, WAIT_PRODUCT_TYPE, WAIT_PRODUCT_TIME = range(3)

PRODUCT_TYPE_LABELS = {
    "cleanser": "Очищение",
    "toner": "Тонер",
    "serum": "Сыворотка",
    "moisturizer": "Крем",
    "spf": "SPF",
    "other": "Другое",
}

TIME_LABELS = {
    "morning": "Утро",
    "evening": "Вечер",
    "both": "Утро и вечер",
}


async def cmd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        products = await get_active_products(session, user_id)

    if not products:
        text = (
            "🧴 *Мои продукты*\n\n"
            "У тебя пока нет добавленных продуктов.\n"
            "Добавь косметику, которой ты пользуешься, и я обновлю твою рутину!"
        )
    else:
        lines = [f"🧴 *Мои продукты* ({len(products)}):\n"]
        for p in products:
            type_label = PRODUCT_TYPE_LABELS.get(p.product_type, p.product_type)
            time_label = TIME_LABELS.get(p.time_of_use, p.time_of_use)
            lines.append(f"• {p.product_name} — {type_label} ({time_label})")
        text = "\n".join(lines)

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=products_list_keyboard(products),
    )


async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *Добавить продукт*\n\nНапиши название продукта:",
        parse_mode="Markdown",
    )
    return WAIT_PRODUCT_NAME


async def receive_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Название слишком короткое. Попробуй ещё раз.")
        return WAIT_PRODUCT_NAME

    context.user_data["new_product"] = {"name": name}
    await update.message.reply_text(
        f"*{name}*\n\nВыбери тип продукта:",
        parse_mode="Markdown",
        reply_markup=product_type_keyboard(),
    )
    return WAIT_PRODUCT_TYPE


async def choose_product_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ptype = query.data.split(":")[1]
    context.user_data["new_product"]["type"] = ptype

    await query.edit_message_text(
        "⏰ Когда используешь этот продукт?",
        reply_markup=product_time_keyboard(),
    )
    return WAIT_PRODUCT_TIME


async def choose_product_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ptime = query.data.split(":")[1]
    user_id = query.from_user.id
    prod = context.user_data.pop("new_product", {})

    async with async_session_factory() as session:
        await add_user_product(
            session=session,
            user_id=user_id,
            product_name=prod["name"],
            product_type=prod["type"],
            time_of_use=ptime,
        )

        # Regenerate routine with updated products
        products = await get_active_products(session, user_id)
        profile = await get_latest_profile(session, user_id)

    if profile:
        try:
            analyzer = get_analyzer()
            products_for_ai = [
                {"product_name": p.product_name, "product_type": p.product_type, "time_of_use": p.time_of_use}
                for p in products
            ]
            routine_result = await analyzer.generate_routine(
                profile={
                    "skin_type": profile.skin_type,
                    "skin_problems": profile.skin_problems or [],
                    "allergies": profile.allergies,
                    "budget": profile.budget,
                    "goal": profile.goal,
                    "age": profile.age,
                },
                user_products=products_for_ai,
            )
            async with async_session_factory() as session:
                await create_routine(
                    session=session,
                    user_id=user_id,
                    morning_steps=routine_result.morning_routine,
                    evening_steps=routine_result.evening_routine,
                    reason_for_change=f"Добавлен продукт: {prod['name']}",
                )
            routine_updated = True
        except Exception as e:
            logger.error(f"Routine update error: {e}", exc_info=True)
            routine_updated = False
    else:
        routine_updated = False

    type_label = PRODUCT_TYPE_LABELS.get(prod["type"], prod["type"])
    time_label = TIME_LABELS.get(ptime, ptime)

    text = (
        f"✅ Продукт добавлен!\n\n"
        f"*{prod['name']}*\n"
        f"Тип: {type_label}\n"
        f"Применение: {time_label}\n"
    )
    if routine_updated:
        text += "\n🔄 Рутина обновлена с учётом нового продукта!"

    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END


async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    async with async_session_factory() as session:
        removed = await remove_user_product(session, product_id, user_id)
        if not removed:
            await query.answer("Продукт не найден.", show_alert=True)
            return
        products = await get_active_products(session, user_id)

    await query.edit_message_reply_markup(reply_markup=products_list_keyboard(products))
    await query.answer("Продукт удалён ✓")


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    await update.message.reply_text("Добавление продукта отменено.")
    return ConversationHandler.END


def get_products_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_product_start, pattern="^add_product$"),
        ],
        states={
            WAIT_PRODUCT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_name),
            ],
            WAIT_PRODUCT_TYPE: [
                CallbackQueryHandler(choose_product_type, pattern="^ptype:"),
            ],
            WAIT_PRODUCT_TIME: [
                CallbackQueryHandler(choose_product_time, pattern="^ptime:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_add)],
        per_message=False,
    )


def get_products_handlers() -> list:
    return [
        CommandHandler("products", cmd_products),
        MessageHandler(filters.Regex("^🧴 Мои продукты$"), cmd_products),
        CallbackQueryHandler(remove_product, pattern="^remove_product:"),
        get_products_handler(),
    ]
