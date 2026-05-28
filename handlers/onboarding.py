"""Onboarding flow: /start → photo → 7 questions → analysis → routine."""
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
    create_routine,
    create_profile_version,
    get_or_create_user,
    save_skin_analysis,
    upsert_reminder,
)
from services import get_analyzer
from utils.keyboards import (
    budget_keyboard,
    confirm_analysis_keyboard,
    goal_keyboard,
    main_menu_keyboard,
    skin_problems_keyboard,
    skin_type_keyboard,
    start_onboarding_keyboard,
    timezone_keyboard,
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
    WAIT_MORNING_TIME,
    WAIT_EVENING_TIME,
    WAIT_TIMEZONE,
    WAIT_CONFIRM,
    WAIT_CORRECTION,
) = range(13)

DISCLAIMER = (
    "⚠️ Анализ носит рекомендательный характер и не является "
    "медицинским заключением. При серьёзных проблемах кожи "
    "обратитесь к дерматологу."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    async with async_session_factory() as session:
        await get_or_create_user(session, user.id, user.full_name)

    # Check referral
    args = context.args
    if args and args[0].startswith("ref_"):
        context.user_data["referrer_id"] = args[0][4:]

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
    context.user_data.setdefault("onboarding", {})

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

    await update.message.reply_text(
        "⏰ *Напоминания*\n\nВ какое время тебе удобно напоминать об *утренней* рутине?\n\n"
        "Напиши в формате *ЧЧ:ММ* _(например: 08:00)_\n"
        "или /skip чтобы пропустить",
        parse_mode="Markdown",
    )
    return WAIT_MORNING_TIME


async def receive_morning_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text.strip()
    if not _validate_time(time_str):
        await update.message.reply_text("Неверный формат. Используй ЧЧ:ММ, например 08:30")
        return WAIT_MORNING_TIME

    context.user_data["onboarding"]["morning_time"] = time_str
    await update.message.reply_text(
        "🌙 В какое время напоминать о *вечерней* рутине?\n\n"
        "Напиши в формате *ЧЧ:ММ* или /skip",
        parse_mode="Markdown",
    )
    return WAIT_EVENING_TIME


async def skip_morning_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["onboarding"]["morning_time"] = None
    await update.message.reply_text(
        "🌙 В какое время напоминать о *вечерней* рутине?\n\n"
        "Напиши в формате *ЧЧ:ММ* или /skip",
        parse_mode="Markdown",
    )
    return WAIT_EVENING_TIME


async def receive_evening_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text.strip()
    if not _validate_time(time_str):
        await update.message.reply_text("Неверный формат. Используй ЧЧ:ММ, например 21:00")
        return WAIT_EVENING_TIME

    context.user_data["onboarding"]["evening_time"] = time_str
    await _ask_timezone(update)
    return WAIT_TIMEZONE


async def skip_evening_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["onboarding"]["evening_time"] = None
    await _ask_timezone(update)
    return WAIT_TIMEZONE


async def _ask_timezone(update: Update) -> None:
    await update.message.reply_text(
        "🌍 Выбери свой часовой пояс:",
        reply_markup=timezone_keyboard(),
    )


async def choose_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tz = query.data.split(":", 1)[1]
    context.user_data["onboarding"]["timezone"] = tz

    await query.edit_message_text("⏳ Анализирую твою кожу... Это займёт несколько секунд.")
    return await _run_analysis(query, context)


async def _run_analysis(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data["onboarding"]
    user_id = query.from_user.id

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
            )
            context.user_data["onboarding"]["analysis_id"] = analysis.id

        problems_text = "\n".join(f"• {p}" for p in result.problems) if result.problems else "• не обнаружено"
        skin_type_labels = {
            "oily": "жирная", "dry": "сухая",
            "combination": "комбинированная", "sensitive": "чувствительная"
        }

        await query.edit_message_text(
            f"🔍 *Результат анализа*\n\n"
            f"*Тип кожи:* {skin_type_labels.get(result.skin_type, result.skin_type)}\n\n"
            f"*Обнаруженные проблемы:*\n{problems_text}\n\n"
            f"*Уверенность анализа:* {int(result.confidence_score * 100)}%\n\n"
            "Всё верно? Или хочешь добавить / исправить?",
            parse_mode="Markdown",
            reply_markup=confirm_analysis_keyboard(),
        )
        return WAIT_CONFIRM

    except Exception as e:
        logger.error(f"Analysis error for user {user_id}: {e}", exc_info=True)
        await query.edit_message_text(
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
        async with async_session_factory() as session:
            # Update analysis with confirmed problems
            analysis_id = data.get("analysis_id")
            if analysis_id:
                from database.queries import update_analysis_user_confirmation
                await update_analysis_user_confirmation(
                    session, analysis_id, confirmed_problems, user_corrections
                )

            # Save profile version
            profile = await create_profile_version(
                session=session,
                user_id=user_id,
                skin_type=data.get("skin_type", "combination"),
                skin_problems=confirmed_problems,
                allergies=data.get("allergies"),
                budget=data.get("budget", "medium"),
                goal=data.get("goal", "hydration"),
                age=data.get("age", 25),
                changed_by="user" if user_corrections else "ai",
                change_reason="Онбординг",
            )

            # Generate routine
            analyzer = get_analyzer()
            routine_result = await analyzer.generate_routine(
                profile={
                    "skin_type": profile.skin_type,
                    "skin_problems": confirmed_problems,
                    "allergies": profile.allergies,
                    "budget": profile.budget,
                    "goal": profile.goal,
                    "age": profile.age,
                },
                user_products=[],
            )

            await create_routine(
                session=session,
                user_id=user_id,
                morning_steps=routine_result.morning_routine,
                evening_steps=routine_result.evening_routine,
                reason_for_change="Первичный анализ",
            )

            # Save reminders
            morning_time = _parse_time(data.get("morning_time"))
            evening_time = _parse_time(data.get("evening_time"))
            if morning_time or evening_time:
                await upsert_reminder(
                    session=session,
                    user_id=user_id,
                    morning_time=morning_time,
                    evening_time=evening_time,
                    timezone=data.get("timezone", "Europe/Moscow"),
                )

        # Format morning routine
        morning_text = _format_routine_steps(routine_result.morning_routine)
        evening_text = _format_routine_steps(routine_result.evening_routine)

        await query.edit_message_text(
            f"🌟 *Твоя персональная рутина готова!*\n\n"
            f"🌅 *Утренний уход:*\n{morning_text}\n\n"
            f"🌙 *Вечерний уход:*\n{evening_text}\n\n"
            f"_{DISCLAIMER}_",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

        # Send main menu message
        await context.bot.send_message(
            chat_id=user_id,
            text="Используй меню ниже для навигации 👇",
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


def _validate_time(time_str: str) -> bool:
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return False
        h, m = int(parts[0]), int(parts[1])
        return 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        return False


def _parse_time(time_str: Optional[str]):
    if not time_str:
        return None
    try:
        from datetime import time
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return None


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("onboarding", None)
    await update.message.reply_text(
        "Онбординг отменён. Напиши /start чтобы начать заново."
    )
    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
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
            WAIT_MORNING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_morning_time),
                CommandHandler("skip", skip_morning_time),
            ],
            WAIT_EVENING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_evening_time),
                CommandHandler("skip", skip_evening_time),
            ],
            WAIT_TIMEZONE: [
                CallbackQueryHandler(choose_timezone, pattern="^tz:"),
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
