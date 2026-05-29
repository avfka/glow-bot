"""Product search — AI-подбор продуктов по категории и профилю."""
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
from database.repositories.profiles import get_latest_profile
from services.products import add_product_and_refresh_routine
from services.product_recommendations import get_product_recommendations
from utils.keyboards import (
    CATEGORY_LABELS,
    product_category_keyboard,
    product_search_empty_keyboard,
    search_results_keyboard,
    product_recommendation_keyboard,
)

logger = logging.getLogger(__name__)

WAIT_CATEGORY, WAIT_PICK = range(2)

async def cmd_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        profile = await get_latest_profile(session, user_id)

    if not profile:
        await update.message.reply_text(
            "🔍 Сначала нужно создать профиль кожи.\n\n"
            "После анализа я смогу подобрать продукты под твой тип кожи и цель ухода.",
            reply_markup=product_search_empty_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 *Подбор продуктов*\n\n"
        "Выбери категорию — я подберу лучшие варианты под твой профиль:",
        parse_mode="Markdown",
        reply_markup=product_category_keyboard(),
    )
    return WAIT_CATEGORY


async def btn_back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔍 *Подбор продуктов*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=product_category_keyboard(),
    )
    return WAIT_CATEGORY


async def btn_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.split(":")[1]
    user_id = query.from_user.id

    context.user_data["search_category"] = category
    cat_label = CATEGORY_LABELS.get(category, category)

    await query.edit_message_text(f"⏳ Подбираю {cat_label} под твой профиль...")

    async with async_session_factory() as session:
        profile = await get_latest_profile(session, user_id)

    try:
        recommendations = await get_product_recommendations(
            profile,
            category_label=cat_label,
        )
        context.user_data["recommendations"] = recommendations

        if not recommendations:
            await query.edit_message_text(
                "😔 Не удалось подобрать продукты. Попробуй другую категорию.",
                parse_mode="Markdown",
                reply_markup=product_category_keyboard(),
            )
            return WAIT_CATEGORY

        text = _format_recommendations_list(recommendations, cat_label)
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=search_results_keyboard(recommendations),
        )
        return WAIT_PICK

    except Exception as e:
        logger.error(f"Product search error for user {user_id}: {e}", exc_info=True)
        await query.edit_message_text(
            "😔 Ошибка при подборе. Попробуй ещё раз.",
            reply_markup=product_category_keyboard(),
        )
        return WAIT_CATEGORY


async def btn_pick_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = _parse_callback_index(query.data)
    if idx is None:
        await query.answer("Кнопка устарела", show_alert=True)
        return WAIT_PICK

    recommendations = context.user_data.get("recommendations", [])

    if idx >= len(recommendations):
        await query.answer("Подборка устарела. Запусти поиск заново.", show_alert=True)
        return WAIT_PICK

    rec = recommendations[idx]
    name = rec.get("name", "")
    brand = rec.get("brand", "")
    full_name = f"{brand} {name}".strip()
    why = rec.get("why", "")
    key_ingredients = rec.get("key_ingredients", [])
    price = rec.get("price_range", "")

    ingredients_text = ""
    if key_ingredients:
        ingredients_text = "\n*Ключевые ингредиенты:*\n" + "\n".join(f"• {i}" for i in key_ingredients[:3])

    wb_query = full_name.replace(" ", "+")

    await query.edit_message_text(
        f"✨ *{full_name}*\n\n"
        f"💡 *Почему подходит:*\n{why}\n"
        f"{ingredients_text}\n\n"
        f"💰 Цена: {price}\n\n"
        "Добавить в рутину?",
        parse_mode="Markdown",
        reply_markup=product_recommendation_keyboard(idx, wb_query=wb_query),
    )
    return WAIT_PICK


async def btn_add_to_routine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    idx = _parse_callback_index(query.data)
    if idx is None:
        await query.answer("Кнопка устарела", show_alert=True)
        return WAIT_PICK

    user_id = query.from_user.id
    recommendations = context.user_data.get("recommendations", [])
    category = context.user_data.get("search_category", "other")

    if idx >= len(recommendations):
        await query.answer("Подборка устарела. Запусти поиск заново.", show_alert=True)
        return WAIT_PICK

    rec = recommendations[idx]
    full_name = f"{rec.get('brand', '')} {rec.get('name', '')}".strip()
    time_of_use = rec.get("time_of_use", "both")

    result = await add_product_and_refresh_routine(
        user_id=user_id,
        product_name=full_name,
        product_type=category,
        time_of_use=time_of_use,
    )
    routine_text = "\n🔄 Рутина обновлена!" if result.routine_updated else ""

    await query.edit_message_text(
        f"✅ *{full_name}* добавлен в твои продукты!{routine_text}\n\n"
        "Хочешь подобрать ещё что-то?",
        parse_mode="Markdown",
        reply_markup=product_category_keyboard(),
    )
    return WAIT_CATEGORY


def _format_recommendations_list(recs: list, cat_label: str) -> str:
    lines = [f"✨ *Подборка: {cat_label}*\n"]
    for i, rec in enumerate(recs, 1):
        name = f"{rec.get('brand', '')} {rec.get('name', '')}".strip()
        price = rec.get("price_range", "")
        lines.append(f"*{i}. {name}*")
        if price:
            lines.append(f"   💰 {price}")
        lines.append("")
    lines.append("Нажми на продукт для подробностей:")
    return "\n".join(lines)


def _parse_callback_index(data: str) -> int | None:
    try:
        return int(data.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("recommendations", None)
    context.user_data.pop("search_category", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Поиск отменён.")
    else:
        await update.message.reply_text("Поиск отменён.")
    return ConversationHandler.END


def get_product_search_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("search", cmd_product_search),
            MessageHandler(filters.Regex("^🔍 Подбор продуктов$"), cmd_product_search),
        ],
        states={
            WAIT_CATEGORY: [
                CallbackQueryHandler(btn_select_category, pattern="^search_cat:"),
                CallbackQueryHandler(btn_back_to_categories, pattern="^search:back$"),
            ],
            WAIT_PICK: [
                CallbackQueryHandler(btn_pick_recommendation, pattern="^pick_rec:"),
                CallbackQueryHandler(btn_add_to_routine, pattern="^add_rec:"),
                CallbackQueryHandler(btn_back_to_categories, pattern="^search:back$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_search),
            CallbackQueryHandler(cancel_search, pattern="^cancel:search$"),
        ],
        per_message=False,
    )
