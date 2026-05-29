from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# -- Reply keyboard (main menu) ------------------------------------------------

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("👤 Профиль"), KeyboardButton("🔍 Подбор продуктов")],
            [KeyboardButton("💆 Моя рутина"), KeyboardButton("🔍 Сканер состава")],
            [KeyboardButton("🧴 Мои продукты"), KeyboardButton("🏆 Лидерборд")],
            [KeyboardButton("⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


# ── Onboarding ────────────────────────────────────────────────────────────────

def start_onboarding_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Начать анализ", callback_data="onboarding:start")]
    ])


def existing_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Подобрать продукты", callback_data="search:start")],
        [InlineKeyboardButton("✏️ Обновить профиль кожи", callback_data="onboarding:start")],
        [InlineKeyboardButton("⏰ Настроить напоминания", callback_data="settings:reminders")],
    ])


def routine_ready_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отметить выполнение", callback_data="routine:track")],
        [
            InlineKeyboardButton("🔍 Подобрать продукты", callback_data="search:start"),
            InlineKeyboardButton("➕ Добавить свой", callback_data="add_product"),
        ],
        [InlineKeyboardButton("⏰ Настроить напоминания", callback_data="settings:reminders")],
    ])


def cancel_flow_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Отмена", callback_data=callback_data)],
    ])


def skin_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💧 Сухая", callback_data="skin_type:dry"),
            InlineKeyboardButton("✨ Жирная", callback_data="skin_type:oily"),
        ],
        [
            InlineKeyboardButton("🔄 Комбинированная", callback_data="skin_type:combination"),
            InlineKeyboardButton("🌸 Чувствительная", callback_data="skin_type:sensitive"),
        ],
    ])


SKIN_PROBLEMS = [
    ("Акне", "acne"),
    ("Розацеа", "rosacea"),
    ("Купероз", "couperose"),
    ("Пигментация", "pigmentation"),
    ("Морщины", "wrinkles"),
    ("Покраснения", "redness"),
    ("Расширенные поры", "enlarged_pores"),
    ("Сухость", "dryness"),
    ("Жирный блеск", "oiliness"),
    ("Экзема", "eczema"),
    ("Псориаз", "psoriasis"),
    ("Чувствительность", "sensitivity"),
    ("Отёчность", "puffiness"),
]


def skin_problems_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for label, code in SKIN_PROBLEMS:
        check = "✅ " if code in selected else ""
        rows.append([InlineKeyboardButton(f"{check}{label}", callback_data=f"problem:{code}")])
    rows.append([InlineKeyboardButton("➡️ Готово", callback_data="problems:done")])
    return InlineKeyboardMarkup(rows)


def budget_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Бюджетный (до 500 ₽)", callback_data="budget:low")],
        [InlineKeyboardButton("💳 Средний (500–2000 ₽)", callback_data="budget:medium")],
        [InlineKeyboardButton("💎 Премиум (от 2000 ₽)", callback_data="budget:high")],
    ])


def goal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💧 Увлажнение", callback_data="goal:hydration")],
        [InlineKeyboardButton("🌟 Выравнивание тона", callback_data="goal:tone")],
        [InlineKeyboardButton("⏳ Антивозрастной уход", callback_data="goal:anti-age")],
    ])


def confirm_analysis_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Верно", callback_data="confirm:yes"),
            InlineKeyboardButton("✏️ Исправить", callback_data="confirm:edit"),
        ]
    ])


# ── Routine ───────────────────────────────────────────────────────────────────

def routine_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌅 Утро", callback_data="routine:morning"),
            InlineKeyboardButton("🌙 Вечер", callback_data="routine:evening"),
        ],
        [InlineKeyboardButton("✅ Отметить выполнение", callback_data="routine:track")],
    ])


def routine_steps_keyboard(steps: list, period: str, step_products: dict) -> InlineKeyboardMarkup:
    """Кнопки для каждого шага рутины — привязать продукт."""
    rows = []
    for i, step in enumerate(steps):
        product = step_products.get(f"{period}_{i}", "")
        label = f"{'✅' if product else '➕'} Шаг {i+1}: {step.get('name', '')}"
        rows.append([InlineKeyboardButton(label, callback_data=f"assign_product:{period}:{i}")])
    rows.append([InlineKeyboardButton("🔍 Подобрать продукт", callback_data="search:start")])
    rows.append([InlineKeyboardButton("✅ Отметить выполнение", callback_data="routine:track")])
    return InlineKeyboardMarkup(rows)


def tracking_keyboard(morning_done: bool, evening_done: bool) -> InlineKeyboardMarkup:
    morning_icon = "✅" if morning_done else "☐"
    evening_icon = "✅" if evening_done else "☐"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{morning_icon} Утро", callback_data="track:morning"),
            InlineKeyboardButton(f"{evening_icon} Вечер", callback_data="track:evening"),
        ],
        [InlineKeyboardButton("💾 Сохранить отметку", callback_data="track:save")],
    ])


def reminder_done_keyboard(period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"✅ Отметить {'утреннюю' if period == 'morning' else 'вечернюю'} рутину выполненной",
            callback_data=f"quick_track:{period}"
        )]
    ])


# ── Profile ───────────────────────────────────────────────────────────────────

def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отметить выполнение", callback_data="routine:track"),
            InlineKeyboardButton("➕ Добавить продукт", callback_data="add_product"),
        ],
        [InlineKeyboardButton("🔍 Подобрать продукты", callback_data="search:start")],
        [InlineKeyboardButton("✏️ Обновить профиль кожи", callback_data="profile:update")],
        [InlineKeyboardButton("⏰ Настроить напоминания", callback_data="settings:reminders")],
    ])


def product_saved_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌅 Утренняя рутина", callback_data="routine:morning"),
            InlineKeyboardButton("🌙 Вечерняя рутина", callback_data="routine:evening"),
        ],
        [
            InlineKeyboardButton("🔍 Подобрать ещё", callback_data="search:start"),
            InlineKeyboardButton("➕ Добавить свой", callback_data="add_product"),
        ],
    ])


# ── Product search ────────────────────────────────────────────────────────────

PRODUCT_CATEGORIES = [
    ("🧼 Очищение", "cleanser"),
    ("💦 Тонер", "toner"),
    ("💉 Сыворотка", "serum"),
    ("🥛 Крем", "moisturizer"),
    ("☀️ SPF", "spf"),
    ("👁 Уход за глазами", "eye_care"),
    ("🌿 Маска", "mask"),
    ("📦 Другое", "other"),
]

CATEGORY_LABELS = {c: l for l, c in PRODUCT_CATEGORIES}


def product_category_keyboard() -> InlineKeyboardMarkup:
    rows = []
    cats = list(PRODUCT_CATEGORIES)
    for i in range(0, len(cats), 2):
        row = [InlineKeyboardButton(cats[i][0], callback_data=f"search_cat:{cats[i][1]}")]
        if i + 1 < len(cats):
            row.append(InlineKeyboardButton(cats[i+1][0], callback_data=f"search_cat:{cats[i+1][1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("Отмена", callback_data="cancel:search")])
    return InlineKeyboardMarkup(rows)


def product_search_empty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Начать анализ", callback_data="onboarding:start")],
    ])


def product_recommendation_keyboard(idx: int, marketplace_urls: dict[str, str] | None = None) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("➕ Добавить в рутину", callback_data=f"add_rec:{idx}")],
    ]
    marketplace_urls = marketplace_urls or {}
    shop_buttons = []
    if marketplace_urls.get("wb"):
        shop_buttons.append(InlineKeyboardButton("WB", url=marketplace_urls["wb"]))
    if marketplace_urls.get("ozon"):
        shop_buttons.append(InlineKeyboardButton("Ozon", url=marketplace_urls["ozon"]))
    if marketplace_urls.get("goldapple"):
        shop_buttons.append(InlineKeyboardButton("ЗЯ", url=marketplace_urls["goldapple"]))
    if shop_buttons:
        rows.append(shop_buttons)
    return InlineKeyboardMarkup(rows)


def search_results_keyboard(recommendations: list) -> InlineKeyboardMarkup:
    rows = []
    for i, rec in enumerate(recommendations):
        name = rec.get("name", f"Продукт {i+1}")[:40]
        rows.append([InlineKeyboardButton(f"{'✅' if rec.get('selected') else '○'} {name}", callback_data=f"pick_rec:{i}")])
    rows.append([InlineKeyboardButton("🔄 Другая категория", callback_data="search:back")])
    rows.append([InlineKeyboardButton("Отмена", callback_data="cancel:search")])
    return InlineKeyboardMarkup(rows)


# ── Leaderboard ───────────────────────────────────────────────────────────────

def leaderboard_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Пригласить подругу", switch_inline_query=referral_link)],
        [InlineKeyboardButton("🏅 Мои достижения", callback_data="league:achievements")],
    ])


def achievements_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="league:back")],
    ])


# ── Scanner ───────────────────────────────────────────────────────────────────

def scanner_result_keyboard(marketplace_urls: dict[str, str] | None = None) -> InlineKeyboardMarkup:
    rows = []
    marketplace_urls = marketplace_urls or {}
    shop_buttons = []
    if marketplace_urls.get("wb"):
        shop_buttons.append(InlineKeyboardButton("WB", url=marketplace_urls["wb"]))
    if marketplace_urls.get("ozon"):
        shop_buttons.append(InlineKeyboardButton("Ozon", url=marketplace_urls["ozon"]))
    if marketplace_urls.get("goldapple"):
        shop_buttons.append(InlineKeyboardButton("ЗЯ", url=marketplace_urls["goldapple"]))
    if shop_buttons:
        rows.append(shop_buttons)
    rows.append([InlineKeyboardButton("🔍 Сканировать ещё", callback_data="scanner:new")])
    return InlineKeyboardMarkup(rows)


def scan_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Ввести название", callback_data="scan:by_name")],
        [InlineKeyboardButton("📷 Сфотографировать состав", callback_data="scan:by_photo")],
        [InlineKeyboardButton("Отмена", callback_data="cancel:scan")],
    ])


def scan_retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Сфотографировать ещё раз", callback_data="scan:by_photo")],
        [InlineKeyboardButton("📝 Ввести название", callback_data="scan:by_name")],
        [InlineKeyboardButton("Отмена", callback_data="cancel:scan")],
    ])


# ── Settings ──────────────────────────────────────────────────────────────────

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ Изменить время напоминаний", callback_data="settings:reminders")],
        [InlineKeyboardButton("👤 Обновить профиль кожи", callback_data="settings:profile")],
    ])


def timezone_keyboard() -> InlineKeyboardMarkup:
    timezones = [
        ("🇷🇺 Москва (UTC+3)", "Europe/Moscow"),
        ("🇷🇺 Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
        ("🇷🇺 Новосибирск (UTC+7)", "Asia/Novosibirsk"),
        ("🇷🇺 Владивосток (UTC+10)", "Asia/Vladivostok"),
        ("🇧🇾 Минск (UTC+3)", "Europe/Minsk"),
        ("🇰🇿 Алматы (UTC+6)", "Asia/Almaty"),
    ]
    rows = [[InlineKeyboardButton(label, callback_data=f"tz:{tz}")] for label, tz in timezones]
    rows.append([InlineKeyboardButton("Отмена", callback_data="cancel:settings")])
    return InlineKeyboardMarkup(rows)


# ── Product type (add product) ────────────────────────────────────────────────

def product_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧼 Очищение", callback_data="ptype:cleanser"),
            InlineKeyboardButton("💦 Тонер", callback_data="ptype:toner"),
        ],
        [
            InlineKeyboardButton("💉 Сыворотка", callback_data="ptype:serum"),
            InlineKeyboardButton("🥛 Крем", callback_data="ptype:moisturizer"),
        ],
        [
            InlineKeyboardButton("☀️ SPF", callback_data="ptype:spf"),
            InlineKeyboardButton("📦 Другое", callback_data="ptype:other"),
        ],
        [InlineKeyboardButton("Отмена", callback_data="cancel:products")],
    ])


def product_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌅 Утро", callback_data="ptime:morning"),
            InlineKeyboardButton("🌙 Вечер", callback_data="ptime:evening"),
            InlineKeyboardButton("🔄 Оба", callback_data="ptime:both"),
        ],
        [InlineKeyboardButton("Отмена", callback_data="cancel:products")],
    ])


def products_list_keyboard(products: list) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        rows.append([
            InlineKeyboardButton(
                f"❌ {p.product_name[:30]}",
                callback_data=f"remove_product:{p.id}"
            )
        ])
    rows.append([InlineKeyboardButton("➕ Добавить продукт", callback_data="add_product")])
    return InlineKeyboardMarkup(rows)
