"""Product ingredient scanner handler."""
import base64
import logging
from typing import Optional

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
    add_catalog_product,
    get_latest_profile,
    increment_scan_count,
    save_product_scan,
    search_catalog,
)
from services import get_analyzer
from services.ingredient_scorer import parse_ingredients_string, score_product
from utils.keyboards import scan_method_keyboard, scanner_result_keyboard

logger = logging.getLogger(__name__)

WAIT_SCAN_QUERY, WAIT_SCAN_PHOTO = range(2)

DISCLAIMER_SHORT = "⚠️ Носит рекомендательный характер"


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🔍 *Сканер состава*\n\n"
        "Как хочешь найти продукт?",
        parse_mode="Markdown",
        reply_markup=scan_method_keyboard(),
    )
    return WAIT_SCAN_QUERY


async def btn_scan_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔍 Введи название продукта или бренда:",
    )
    context.user_data["scan_method"] = "name"
    return WAIT_SCAN_QUERY


async def btn_scan_by_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📷 Сфотографируй состав на упаковке продукта.\n\n"
        "_Совет: снимай при хорошем освещении, чтобы текст был чётким_",
        parse_mode="Markdown",
    )
    context.user_data["scan_method"] = "photo"
    return WAIT_SCAN_PHOTO


async def receive_scan_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query_text = update.message.text.strip()
    user_id = update.effective_user.id

    async with async_session_factory() as session:
        products = await search_catalog(session, query_text)

    if products:
        product = products[0]
        async with async_session_factory() as session:
            await increment_scan_count(session, product.id)
            profile = await get_latest_profile(session, user_id)

        if product.ingredients_parsed and profile:
            profile_dict = {
                "skin_type": profile.skin_type,
                "skin_problems": profile.skin_problems or [],
                "allergies": profile.allergies,
            }
            async with async_session_factory() as session:
                score_result = await score_product(
                    session, product.ingredients_parsed, profile_dict
                )

            result_text = _format_scan_result(
                product_name=f"{product.brand or ''} {product.name}".strip(),
                score=score_result.score,
                good=score_result.good,
                neutral=score_result.neutral,
                warnings=score_result.warnings,
                bad=score_result.bad,
                ph=product.ph,
            )

            async with async_session_factory() as session:
                await save_product_scan(
                    session=session,
                    user_id=user_id,
                    product_name=product.name,
                    ingredients_raw=product.ingredients_raw or "",
                    ingredients_parsed=product.ingredients_parsed or [],
                    score=score_result.score,
                    suitable=score_result.suitable,
                    warnings=[
                        {"name": w.name, "reason": w.reason} for w in score_result.bad + score_result.warnings
                    ],
                    product_id=product.id,
                )

            await update.message.reply_text(
                result_text,
                parse_mode="Markdown",
                reply_markup=scanner_result_keyboard(
                    wb_url=product.wb_url,
                    za_url=product.za_url,
                ),
            )
            return ConversationHandler.END

    # Product not found — ask for photo
    context.user_data["pending_product_name"] = query_text
    await update.message.reply_text(
        f"Продукт *«{query_text}»* не найден в базе.\n\n"
        "📷 Сфотографируй состав на упаковке, и я проанализирую его!",
        parse_mode="Markdown",
    )
    return WAIT_SCAN_PHOTO


async def receive_scan_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    photo_bytes = await file.download_as_bytearray()
    photo_b64 = base64.b64encode(photo_bytes).decode()

    await update.message.reply_text("⏳ Читаю состав...")

    try:
        analyzer = get_analyzer()
        ingredients_raw = await analyzer.extract_ingredients_from_image(photo_b64)

        if not ingredients_raw or len(ingredients_raw) < 10:
            await update.message.reply_text(
                "😔 Не удалось прочитать состав. Попробуй ещё раз при лучшем освещении."
            )
            return WAIT_SCAN_PHOTO

        ingredients_list = parse_ingredients_string(ingredients_raw)
        product_name = context.user_data.pop("pending_product_name", "Неизвестный продукт")

        async with async_session_factory() as session:
            profile = await get_latest_profile(session, user_id)

        if profile:
            profile_dict = {
                "skin_type": profile.skin_type,
                "skin_problems": profile.skin_problems or [],
                "allergies": profile.allergies,
            }
            async with async_session_factory() as session:
                score_result = await score_product(session, ingredients_list, profile_dict)

            # Try AI scoring for more detail
            try:
                openai_result = await analyzer.score_product_for_profile(
                    product_name=product_name,
                    ingredients_list=ingredients_list,
                    profile=profile_dict,
                )
                score = openai_result.get("score", score_result.score)
                good_ais = [
                    type("", (), {"name": i["name"], "reason": i.get("benefit", ""), "ru_name": ""})()
                    for i in openai_result.get("good_ingredients", [])
                ]
                warn_ais = [
                    type("", (), {"name": i["name"], "reason": i.get("reason", ""), "ru_name": ""})()
                    for i in openai_result.get("bad_ingredients", [])
                ]
                neutral_ais = [
                    type("", (), {"name": i["name"], "reason": "", "ru_name": ""})()
                    for i in openai_result.get("neutral_ingredients", [])
                ]
                ph_comment = openai_result.get("ph_comment", "")
            except Exception:
                score = score_result.score
                good_ais = score_result.good
                warn_ais = score_result.bad + score_result.warnings
                neutral_ais = score_result.neutral
                ph_comment = ""

            result_text = _format_scan_result(
                product_name=product_name,
                score=score,
                good=good_ais,
                neutral=neutral_ais,
                warnings=warn_ais,
                bad=[],
                ph=None,
                ph_comment=ph_comment,
            )
        else:
            result_text = (
                f"📋 *{product_name}*\n\n"
                f"Обнаружено ингредиентов: {len(ingredients_list)}\n\n"
                "Чтобы получить персональную оценку — сначала пройди анализ кожи (/start)"
            )

        # Save to catalog
        async with async_session_factory() as session:
            catalog_product = await add_catalog_product(
                session=session,
                name=product_name,
                brand=None,
                category="other",
                ingredients_raw=ingredients_raw,
                ingredients_parsed=ingredients_list,
                source="user_ocr",
                verified=False,
            )
            if profile:
                await save_product_scan(
                    session=session,
                    user_id=user_id,
                    product_name=product_name,
                    ingredients_raw=ingredients_raw,
                    ingredients_parsed=ingredients_list,
                    score=score if profile else 0,
                    suitable=score >= 50 if profile else True,
                    warnings=[],
                    product_id=catalog_product.id,
                )

        await update.message.reply_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=scanner_result_keyboard(),
        )

    except Exception as e:
        logger.error(f"Scan error for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "😔 Ошибка при анализе состава. Попробуй ещё раз."
        )

    return ConversationHandler.END


def _format_scan_result(
    product_name: str,
    score: int,
    good: list,
    neutral: list,
    warnings: list,
    bad: list,
    ph: Optional[float] = None,
    ph_comment: str = "",
) -> str:
    lines = [
        f"*{product_name}*",
        f"Подходит тебе на *{score}/100*\n",
    ]

    if good:
        lines.append("🟢 *Хорошо для твоей кожи:*")
        for ing in good[:5]:
            name = ing.name
            reason = getattr(ing, "reason", "") or getattr(ing, "benefit", "")
            ru = getattr(ing, "ru_name", "")
            label = f"{name}"
            if ru:
                label += f" ({ru})"
            if reason:
                label += f" — {reason}"
            lines.append(f"• {label}")
        lines.append("")

    if neutral:
        lines.append("🟡 *Нейтрально:*")
        for ing in neutral[:3]:
            lines.append(f"• {ing.name}")
        lines.append("")

    if warnings:
        lines.append("🔴 *Осторожно:*")
        for ing in (warnings + bad)[:5]:
            name = ing.name
            reason = getattr(ing, "reason", "")
            label = name
            if reason:
                label += f" — {reason}"
            lines.append(f"• {label}")
        lines.append("")

    if ph is not None:
        lines.append(f"💡 *pH: {ph}*")
        if ph <= 5.5:
            lines.append("оптимально для кожи\n")
        else:
            lines.append("выше нейтрального\n")
    elif ph_comment:
        lines.append(f"💡 {ph_comment}\n")

    lines.append(f"_{DISCLAIMER_SHORT}_")
    return "\n".join(lines)


async def btn_scanner_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔍 Как хочешь найти продукт?",
        reply_markup=scan_method_keyboard(),
    )
    return WAIT_SCAN_QUERY


async def cancel_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("pending_product_name", None)
    context.user_data.pop("scan_method", None)
    await update.message.reply_text("Сканирование отменено.")
    return ConversationHandler.END


def get_scanner_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("scan", cmd_scan),
            MessageHandler(filters.Regex("^🔍 Сканер состава$"), cmd_scan),
        ],
        states={
            WAIT_SCAN_QUERY: [
                CallbackQueryHandler(btn_scan_by_name, pattern="^scan:by_name$"),
                CallbackQueryHandler(btn_scan_by_photo, pattern="^scan:by_photo$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_scan_query),
                CallbackQueryHandler(btn_scanner_new, pattern="^scanner:new$"),
            ],
            WAIT_SCAN_PHOTO: [
                MessageHandler(filters.PHOTO, receive_scan_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_scan)],
        per_message=False,
    )
