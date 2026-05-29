"""Onboarding flow: /start → photo → 7 questions → analysis → routine."""
import base64
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
from database.repositories.profiles import get_latest_profile, save_skin_analysis
from database.repositories.users import get_or_create_user
from services import get_analyzer
from services.onboarding import complete_onboarding
from utils.keyboards import (
    budget_keyboard,
    confirm_analysis_keyboard,
    existing_profile_keyboard,
    goal_keyboard,
    main_menu_keyboard,
    routine_ready_keyboard,
    skin_problems_keyboard,
    skin_type_keyboard,
    start_onboarding_keyboard,
)

logger = logging.getLogger(__name__)

# Conversation states
(
    WAIT_START,
    WAIT_PHOTO,
    WAIT_SKIN_TYPE,
    WAIT_PROBLEMS,
    WAIT_ALLERGIES,
    WAIT_BUDGET,
    WAIT_GOAL,
    WAIT_AGE,
    WAIT_CONFIRM,
    WAIT_CORRECTION,
) = range(10)

PROBLEMS_RU = {
    "acne": "Акне",
    "rosacea": "Розацеа",
    "couperose": "Купероз",
    "pigmentation": "Пигментация",
    "wrinkles": "Морщины",
    "redness": "Покраснения",
    "enlarged_pores": "Расширенные поры",
    "dryness": "Сухость",
    "oiliness": "Жирный блеск",
    "eczema": "Экзема",
    "psoriasis": "Псориаз",
    "sensitivity": "Чувствительность",
    "puffiness": "Отёчность",
}

DISCLAIMER = (
    "⚠️ Анализ носит рекомендательный характер и не является "
    "медицинским заключением. При серьёзных проблемах кожи "
    "обратитесь к дерматологу."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    async with async_session_factory() as session:
        await get_or_create_user(
            session, user.id, user.full_name, commit=False
        )
        await session.commit()
        profile = await get_latest_profile(session, user.id)

    # Check referral
    args = context.args
    if args and args[0].startswith("ref_"):
        context.user_data["referrer_id"] = args[0][4:]

    if profile:
        await update.message.reply_text(
            f"👋 {user.first_name}, профиль кожи уже готов.\n\n"
            "Что можно сделать сейчас:\n"
            "• открыть рутину ухода\n"
            "• проверить состав продукта\n"
            "• подобрать косметику\n"
            "• обновить профиль, если кожа изменилась",
            reply_markup=main_menu_keyboard(),
        )
        await update.message.reply_text(
            "Для повторного анализа нажми кнопку ниже.",
            reply_markup=existing_profile_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — *GlowBot*, твой персональный AI-косметолог 🌸\n\n"
        "Я помогу тебе:\n"
        "• Проанализировать состояние кожи\n"
        "• Составить персональную рутину ухода\n"
        "• Отслеживать прогресс и напоминать о процедурах\n"
        "• Проверить состав косметики\n\n"
        f"{DISCLAIMER}\n\n"
        "Готова начать?",
        parse_mode="Markdown",
        reply_markup=start_onboarding_keyboard(),
    )
    return WAIT_START


async def onboarding_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["onboarding"] = {}

    await query.edit_message_text(
        "📸 *Шаг 1 из 7 — Фото кожи*\n\n"
        "Пришли фото своего лица в анфас при естественном освещении.\n\n"
        "💡 _Советы_:\n"
        "• Снимай при дневном свете\n"
        "• Без макияжа, чистая кожа\n"
        "• Камера на уровне лица\n\n"
        "Можешь пропустить этот шаг, нажав /skip",
        parse_mode="Markdown",
    )
    return WAIT_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1]
    file = await photo.get_file()
    photo_bytes = await file.download_as_bytearray()
    photo_b64 = base64.b64encode(photo_bytes).decode()

    context.user_data["onboarding"]["photo_b64"] = photo_b64
    context.user_data["onboarding"]["photo_path"] = file.file_path

    await update.message.reply_text(
        "✅ Фото получено!\n\n"
        "*Шаг 2 из 7 — Тип кожи*\n\n"
        "Какой у тебя тип кожи?",
        parse_mode="Markdown",
        reply_markup=skin_type_keyboard(),
    )
    return WAIT_SKIN_TYPE


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["onboarding"]["photo_b64"] = None
    context.user_data["onboarding"]["photo_path"] = None

    await update.message.reply_text(
        "*Шаг 2 из 7 — Тип кожи*\n\nКакой у тебя тип кожи?",
        parse_mode="Markdown",
        reply_markup=skin_type_keyboard(),
    )
    return WAIT_SKIN_TYPE


async def choose_skin_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    skin_type = query.data.split(":")[1]
    context.user_data["onboarding"]["skin_type"] = skin_type
    context.user_data["onboarding"]["problems"] = []

    await query.edit_message_text(
        "*Шаг 3 из 7 — Проблемы кожи*\n\n"
        "Выбери все проблемы, которые тебя беспокоят.\n"
        "_(можно выбрать несколько)_",
        parse_mode="Markdown",
        reply_markup=skin_problems_keyboard([]),
    )
    return WAIT_PROBLEMS


async def toggle_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    problem = query.data.split(":")[1]
    problems: list = context.user_data["onboarding"].get("problems", [])

    if problem in problems:
        problems.remove(problem)
    else:
        problems.append(problem)
    context.user_data["onboarding"]["problems"] = problems

    await query.edit_message_reply_markup(reply_markup=skin_problems_keyboard(problems))
    return WAIT_PROBLEMS


async def problems_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "*Шаг 4 из 7 — Аллергии*\n\n"
        "Есть ли у тебя аллергия на косметические ингредиенты?\n\n"
        "Напиши через запятую _(например: «ретинол, эфирные масла»)_\n"
        "или отправь /skip если аллергий нет.",
        parse_mode="Markdown",
    )
    return WAIT_ALLERGIES


async def receive_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["onboarding"]["allergies"] = update.message.text
    await _ask_budget(update)
    return WAIT_BUDGET


async def skip_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["onboarding"]["allergies"] = None
    await _ask_budget(update)
    return WAIT_BUDGET


async def _ask_budget(update: Update) -> None:
    await update.message.reply_text(
        "*Шаг 5 из 7 — Бюджет*\n\nКакой бюджет на косметику тебя устраивает?",
        parse_mode="Markdown",
        reply_markup=budget_keyboard(),
    )


async def choose_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["onboarding"]["budget"] = query.data.split(":")[1]

    await query.edit_message_text(
        "*Шаг 6 из 7 — Цель ухода*\n\nЧего ты хочешь достичь?",
        parse_mode="Markdown",
        reply_markup=goal_keyboard(),
    )
    return WAIT_GOAL


async def choose_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["onboarding"]["goal"] = query.data.split(":")[1]

    await query.edit_message_text(
        "*Шаг 7 из 7 — Возраст*\n\nСколько тебе лет?\n\n_(просто напиши число)_",
        parse_mode="Markdown",
    )
    return WAIT_AGE


async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit() or not (10 <= int(text) <= 100):
        await update.message.reply_text("Пожалуйста, введи корректный возраст (число от 10 до 100).")
        return WAIT_AGE

    context.user_data["onboarding"]["age"] = int(text)
    context.user_data["onboarding"]["morning_time"] = None
    context.user_data["onboarding"]["evening_time"] = None
    context.user_data["onboarding"]["timezone"] = "Europe/Moscow"

    message = await update.message.reply_text(
        "⏳ Анализирую твою кожу... Это займёт несколько секунд."
    )
    return await _run_analysis(message, context, user_id=update.effective_user.id)


async def _run_analysis(target, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    data = context.user_data["onboarding"]

    try:
        analyzer = get_analyzer()
        result = await analyzer.analyze_skin(
            photo_base64=data.get("photo_b64"),
            skin_type=data.get("skin_type", "combination"),
            problems=data.get("problems", []),
            allergies=data.get("allergies"),
            budget=data.get("budget", "medium"),
            goal=data.get("goal", "hydration"),
            age=data.get("age", 25),
        )
        context.user_data["onboarding"]["analysis_result"] = result

        async with async_session_factory() as session:
            analysis = await save_skin_analysis(
                session=session,
                user_id=user_id,
                photo_path=data.get("photo_path"),
                ai_raw_response=result.raw_response or {},
                ai_detected_problems=result.problems,
                skin_score=result.raw_response.get("skin_score") if result.raw_response else None,
                commit=False,
            )
            await session.commit()
            context.user_data["onboarding"]["analysis_id"] = analysis.id

        problems_text = "\n".join(f"• {PROBLEMS_RU.get(p, p)}" for p in result.problems) if result.problems else "• не обнаружено"
        skin_type_labels = {
            "oily": "жирная", "dry": "сухая",
            "combination": "комбинированная", "sensitive": "чувствительная"
        }

        # Skin score block
        skin_score = result.raw_response.get("skin_score") if result.raw_response else None
        score_text = ""
        if skin_score:
            overall = skin_score.get("overall")
            hydration = skin_score.get("hydration")
            evenness = skin_score.get("evenness")
            pores = skin_score.get("pores")
            if overall is not None:
                score_text = (
                    f"\n*Оценка состояния кожи:*\n"
                    f"• Общая: {overall}/100\n"
                )
                if hydration is not None:
                    score_text += f"• Увлажнённость: {hydration}/100\n"
                if evenness is not None:
                    score_text += f"• Ровность тона: {evenness}/100\n"
                if pores is not None:
                    score_text += f"• Поры: {pores}/100\n"

        # Recommended ingredients block
        rec = result.recommended_ingredients[:5] if result.recommended_ingredients else []
        avoid = result.avoid_ingredients[:3] if result.avoid_ingredients else []
        ingredients_text = ""
        if rec:
            ingredients_text += "\n✅ *Рекомендую ингредиенты:*\n" + "\n".join(f"• {i}" for i in rec)
        if avoid:
            ingredients_text += "\n\n❌ *Лучше избегать:*\n" + "\n".join(f"• {i}" for i in avoid)

        # Difference vs user answers
        user_problems = set(data.get("problems", []))
        ai_problems = set(result.problems)
        added = ai_problems - user_problems
        removed = user_problems - ai_problems
        diff_text = ""
        if added:
            added_ru = ", ".join(PROBLEMS_RU.get(p, p) for p in added)
            diff_text += f"\n💡 *AI дополнительно выявил:* {added_ru}"
        if removed:
            removed_ru = ", ".join(PROBLEMS_RU.get(p, p) for p in removed)
            diff_text += f"\n💡 *AI не подтвердил:* {removed_ru}"

        await target.edit_text(
            f"🔍 *Результат анализа*\n\n"
            f"*Тип кожи:* {skin_type_labels.get(result.skin_type, result.skin_type)}\n\n"
            f"*Обнаруженные проблемы:*\n{problems_text}\n"
            f"{diff_text}"
            f"{score_text}"
            f"{ingredients_text}\n\n"
            f"*Уверенность анализа:* {int(result.confidence_score * 100)}%\n\n"
            "Я использую этот список, чтобы составить рутину. "
            "Всё верно или хочешь исправить?",
            parse_mode="Markdown",
            reply_markup=confirm_analysis_keyboard(),
        )
        return WAIT_CONFIRM

    except Exception as e:
        logger.error(f"Analysis error for user {user_id}: {e}", exc_info=True)
        await target.edit_text(
            "😔 Произошла ошибка при анализе. Попробуем ещё раз?\n\n"
            "Используй /start чтобы начать заново."
        )
        return ConversationHandler.END


async def confirm_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data["onboarding"]

    if query.data == "confirm:yes":
        result = data["analysis_result"]
        problems = result.problems
        return await _save_and_generate_routine(query, context, problems, user_corrections=False)

    # Edit
    problems = data["analysis_result"].problems
    await query.edit_message_text(
        "✏️ *Исправь список проблем*\n\n"
        "Выбери все проблемы, которые тебя беспокоят:",
        parse_mode="Markdown",
        reply_markup=skin_problems_keyboard(problems),
    )
    context.user_data["onboarding"]["corrected_problems"] = list(problems)
    return WAIT_CORRECTION


async def toggle_correction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    problem = query.data.split(":")[1]
    problems: list = context.user_data["onboarding"].get("corrected_problems", [])

    if problem in problems:
        problems.remove(problem)
    else:
        problems.append(problem)
    context.user_data["onboarding"]["corrected_problems"] = problems

    await query.edit_message_reply_markup(reply_markup=skin_problems_keyboard(problems))
    return WAIT_CORRECTION


async def corrections_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    corrected = context.user_data["onboarding"].get("corrected_problems", [])
    return await _save_and_generate_routine(query, context, corrected, user_corrections=True)


async def _save_and_generate_routine(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    confirmed_problems: list,
    user_corrections: bool,
) -> int:
    data = context.user_data["onboarding"]
    user_id = query.from_user.id

    await query.edit_message_text("⏳ Составляю твою персональную рутину...")

    try:
        completion = await complete_onboarding(
            user_id=user_id,
            onboarding_data=data,
            confirmed_problems=confirmed_problems,
            user_corrections=user_corrections,
        )
        routine_result = completion.routine_result

        # Format morning routine
        morning_text = _format_routine_steps(routine_result.morning_routine)
        evening_text = _format_routine_steps(routine_result.evening_routine)

        # edit_message_text не поддерживает ReplyKeyboardMarkup — сначала редактируем без клавиатуры
        await query.edit_message_text(
            f"🌟 *Твоя персональная рутина готова!*\n\n"
            f"🌅 *Утренний уход:*\n{morning_text}\n\n"
            f"🌙 *Вечерний уход:*\n{evening_text}\n\n"
            f"_{DISCLAIMER}_",
            parse_mode="Markdown",
            reply_markup=routine_ready_keyboard(),
        )

        # Отправляем новое сообщение с меню
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "Рутина сохранена. Следующий полезный шаг — добавить свои продукты "
                "или включить напоминания."
            ),
            reply_markup=main_menu_keyboard(),
        )

        context.user_data.pop("onboarding", None)
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Routine generation error for user {user_id}: {e}", exc_info=True)
        await query.edit_message_text(
            "😔 Ошибка при создании рутины. Попробуй позже или напиши /start"
        )
        return ConversationHandler.END


def _format_routine_steps(steps: list) -> str:
    if not steps:
        return "• Рутина пока не заполнена"
    lines = []
    for step in steps:
        lines.append(f"{step.get('step', '•')}. *{step.get('name', '')}*")
        if step.get("description"):
            lines.append(f"   _{step['description']}_")
    return "\n".join(lines)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("onboarding", None)
    await update.message.reply_text(
        "Онбординг отменён. Напиши /start чтобы начать заново."
    )
    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            CallbackQueryHandler(onboarding_start, pattern="^onboarding:start$"),
        ],
        states={
            WAIT_START: [
                CallbackQueryHandler(onboarding_start, pattern="^onboarding:start$"),
            ],
            WAIT_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                CommandHandler("skip", skip_photo),
            ],
            WAIT_SKIN_TYPE: [
                CallbackQueryHandler(choose_skin_type, pattern="^skin_type:"),
            ],
            WAIT_PROBLEMS: [
                CallbackQueryHandler(toggle_problem, pattern="^problem:"),
                CallbackQueryHandler(problems_done, pattern="^problems:done$"),
            ],
            WAIT_ALLERGIES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_allergies),
                CommandHandler("skip", skip_allergies),
            ],
            WAIT_BUDGET: [
                CallbackQueryHandler(choose_budget, pattern="^budget:"),
            ],
            WAIT_GOAL: [
                CallbackQueryHandler(choose_goal, pattern="^goal:"),
            ],
            WAIT_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age),
            ],
            WAIT_CONFIRM: [
                CallbackQueryHandler(confirm_analysis, pattern="^confirm:"),
            ],
            WAIT_CORRECTION: [
                CallbackQueryHandler(toggle_correction, pattern="^problem:"),
                CallbackQueryHandler(corrections_done, pattern="^problems:done$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        per_message=False,
    )
