"""Product search — AI-подбор продуктов по категории и профилю."""
import json
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
from database.queries import add_user_product, get_latest_profile, get_latest_routine, create_routine
from services import get_analyzer
from utils.keyboards import (
    CATEGORY_LABELS,
    main_menu_keyboard,
    product_category_keyboard,
    search_results_keyboard,
    product_recommendation_keyboard,
)

logger = logging.getLogger(__name__)

WAIT_CATEGORY, WAIT_PICK = range(2)

SKIN_TYPE_RU = {
    "oily": "жирная", "dry": "сухая",
    "combination": "комбинированная", "sensitive": "чувствительная",
}
BUDGET_RU = {"low": "до 500 ₽", "medium": "500–2000 ₽", "high": "от 2000 ₽"}
GOAL_RU = {"hydration": "увлажнение", "tone": "выравнивание тона", "anti-age": "антивозрастной"}


async def cmd_product_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    async with async_session_factory() as session:
        profile = await get_latest_profile(session, user_id)

    if not profile:
        await update.message.reply_text(
            "🔍 Сначала нужно создать профиль кожи.\n\nПройди анализ → /start"
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
        analyzer = get_analyzer()
        recommendations = await _get_recommendations(analyzer, profile, category)
        context.user_data["recommendations"] = recommendations

        if not recommendations:
            await query.edit_message_text(
                "😔 Не удалось подобрать продукты. Попробуй другую категорию.",
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
    idx = int(query.data.split(":")[1])
    recommendations = context.user_data.get("recommendations", [])

    if idx >= len(recommendations):
        await query.answer("Продукт не найден", show_alert=True)
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
    idx = int(query.data.split(":")[1])
    user_id = query.from_user.id
    recommendations = context.user_data.get("recommendations", [])
    category = context.user_data.get("search_category", "other")

    if idx >= len(recommendations):
        await query.answer("Продукт не найден", show_alert=True)
        return WAIT_PICK

    rec = recommendations[idx]
    full_name = f"{rec.get('brand', '')} {rec.get('name', '')}".strip()
    time_of_use = rec.get("time_of_use", "both")

    async with async_session_factory() as session:
        await add_user_product(
            session=session,
            user_id=user_id,
            product_name=full_name,
            product_type=category,
            time_of_use=time_of_use,
        )

        # Regenerate routine with new product
        from database.queries import get_active_products
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
                    reason_for_change=f"Добавлен продукт: {full_name}",
                )
            routine_text = "\n🔄 Рутина обновлена!"
        except Exception as e:
            logger.error(f"Routine update error: {e}")
            routine_text = ""
    else:
        routine_text = ""

    await query.edit_message_text(
        f"✅ *{full_name}* добавлен в твои продукты!{routine_text}\n\n"
        "Хочешь подобрать ещё что-то?",
        parse_mode="Markdown",
        reply_markup=product_category_keyboard(),
    )
    return WAIT_CATEGORY


async def _get_recommendations(analyzer, profile, category: str) -> list[dict]:
    """Ask AI for product recommendations."""
    skin_type = SKIN_TYPE_RU.get(profile.skin_type or "combination", profile.skin_type)
    problems = ", ".join(profile.skin_problems or []) or "нет"
    budget = BUDGET_RU.get(profile.budget or "medium", profile.budget)
    goal = GOAL_RU.get(profile.goal or "hydration", profile.goal)
    allergies = profile.allergies or "нет"
    cat_label = CATEGORY_LABELS.get(category, category)

    prompt = (
        f"Порекомендуй 4 реальных продукта категории «{cat_label}» для:\n"
        f"Тип кожи: {skin_type}\n"
        f"Проблемы: {problems}\n"
        f"Цель: {goal}\n"
        f"Бюджет: {budget}\n"
        f"Аллергии: {allergies}\n\n"
        "Только реальные бренды, доступные в России (La Roche-Posay, The Ordinary, Виши, "
        "Bioderma, Garnier, CeraVe, Eucerin, Clinique и т.д.).\n\n"
        "Ответь JSON:\n"
        '{"recommendations": ['
        '{"name": "...", "brand": "...", "why": "почему подходит 1-2 предложения", '
        '"key_ingredients": ["ингредиент1", "ингредиент2"], '
        '"price_range": "от XXX ₽", "time_of_use": "morning|evening|both"}'
        "]}"
    )

    # Use OpenAI directly via analyzer
    from config import settings
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "Ты — косметолог. Рекомендуй реальные продукты. Отвечай только JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
    )
    data = json.loads(response.choices[0].message.content)
    return data.get("recommendations", [])


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


async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("recommendations", None)
    context.user_data.pop("search_category", None)
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
        fallbacks=[CommandHandler("cancel", cancel_search)],
        per_message=False,
    )
