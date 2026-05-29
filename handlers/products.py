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
from database.repositories.products import (
    get_active_products,
    remove_user_product,
)
from services.products import add_product_and_refresh_routine
from utils.keyboards import (
    cancel_flow_keyboard,
    product_time_keyboard,
    product_type_keyboard,
    product_saved_keyboard,
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
        reply_markup=cancel_flow_keyboard("cancel:products"),
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
    product_data = context.user_data.get("new_product")
    if not product_data:
        await query.edit_message_text(
            "Сессия добавления продукта устарела. Открой /products и начни заново."
        )
        return ConversationHandler.END

    product_data["type"] = ptype

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
    prod = context.user_data.pop("new_product", None)
    if not prod or not prod.get("name") or not prod.get("type"):
        await query.edit_message_text(
            "Сессия добавления продукта устарела. Открой /products и начни заново."
        )
        return ConversationHandler.END

    result = await add_product_and_refresh_routine(
        user_id=user_id,
        product_name=prod["name"],
        product_type=prod["type"],
        time_of_use=ptime,
    )

    type_label = PRODUCT_TYPE_LABELS.get(prod["type"], prod["type"])
    time_label = TIME_LABELS.get(ptime, ptime)

    text = (
        f"✅ Продукт добавлен!\n\n"
        f"*{prod['name']}*\n"
        f"Тип: {type_label}\n"
        f"Применение: {time_label}\n"
    )
    if result.routine_updated:
        text += "\n🔄 Рутина обновлена с учётом нового продукта!"

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=product_saved_keyboard(),
    )
    return ConversationHandler.END


async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    async with async_session_factory() as session:
        removed = await remove_user_product(
            session, product_id, user_id, commit=False
        )
        if removed:
            await session.commit()
        if not removed:
            await query.answer("Продукт не найден.", show_alert=True)
            return
        products = await get_active_products(session, user_id)

    await query.edit_message_reply_markup(reply_markup=products_list_keyboard(products))
    await query.answer("Продукт удалён ✓")


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Добавление продукта отменено.")
    else:
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
        fallbacks=[
            CommandHandler("cancel", cancel_add),
            CallbackQueryHandler(cancel_add, pattern="^cancel:products$"),
        ],
        per_message=False,
    )


def get_products_handlers() -> list:
    return [
        CommandHandler("products", cmd_products),
        MessageHandler(filters.Regex("^🧴 Мои продукты$"), cmd_products),
        CallbackQueryHandler(remove_product, pattern="^remove_product:"),
        get_products_handler(),
    ]
