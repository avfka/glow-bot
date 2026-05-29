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

from services import get_analyzer
from services.scanner import scan_catalog_product, scan_ocr_ingredients
from utils.marketplaces import merge_marketplace_urls, marketplace_search_urls
from utils.keyboards import scan_method_keyboard, scan_retry_keyboard, scanner_result_keyboard

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

    scan_result = await scan_catalog_product(user_id=user_id, query_text=query_text)
    if scan_result and scan_result.score is not None:
        product = scan_result.product
        result_text = _format_scan_result(
            product_name=f"{product.brand or ''} {product.name}".strip(),
            score=scan_result.score,
            good=scan_result.good,
            neutral=scan_result.neutral,
            warnings=scan_result.warnings,
            bad=scan_result.bad,
            ph=product.ph,
        )

        await update.message.reply_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=scanner_result_keyboard(
                marketplace_urls=merge_marketplace_urls(
                    f"{product.brand or ''} {product.name}".strip(),
                    wb_url=product.wb_url,
                    za_url=product.za_url,
                ),
            ),
        )
        return ConversationHandler.END

    # Product not found — ask for photo
    context.user_data["pending_product_name"] = query_text
    await update.message.reply_text(
        f"Продукт *«{query_text}»* не найден в базе.\n\n"
        "📷 Сфотографируй состав на упаковке, и я проанализирую его!",
        parse_mode="Markdown",
        reply_markup=scan_retry_keyboard(),
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
                "😔 Не удалось прочитать состав. Попробуй ещё раз при лучшем освещении.",
                reply_markup=scan_retry_keyboard(),
            )
            return WAIT_SCAN_PHOTO

        product_name = context.user_data.pop("pending_product_name", "Неизвестный продукт")
        scan_result = await scan_ocr_ingredients(
            user_id=user_id,
            product_name=product_name,
            ingredients_raw=ingredients_raw,
            analyzer=analyzer,
        )

        if scan_result.profile_exists:
            result_text = _format_scan_result(
                product_name=product_name,
                score=scan_result.score or 0,
                good=scan_result.good,
                neutral=scan_result.neutral,
                warnings=scan_result.warnings,
                bad=scan_result.bad,
                ph=None,
                ph_comment=scan_result.ph_comment,
            )
        else:
            result_text = (
                f"📋 *{product_name}*\n\n"
                f"Обнаружено ингредиентов: {len(scan_result.ingredients_list)}\n\n"
                "Чтобы получить персональную оценку — сначала пройди анализ кожи."
            )

        await update.message.reply_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=scanner_result_keyboard(
                marketplace_urls=marketplace_search_urls(product_name),
            ),
        )

    except Exception as e:
        logger.error(f"Scan error for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "😔 Ошибка при анализе состава. Попробуй ещё раз.",
            reply_markup=scan_retry_keyboard(),
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
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Сканирование отменено.")
    else:
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
                CallbackQueryHandler(btn_scan_by_name, pattern="^scan:by_name$"),
                CallbackQueryHandler(btn_scan_by_photo, pattern="^scan:by_photo$"),
                MessageHandler(filters.PHOTO, receive_scan_photo),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_scan),
            CallbackQueryHandler(cancel_scan, pattern="^cancel:scan$"),
        ],
        per_message=False,
    )
