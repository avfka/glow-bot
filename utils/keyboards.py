from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# ── Reply keyboard (main menu) ────────────────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🌅 Утренняя рутина"), KeyboardButton("🌙 Вечерняя рутина")],
            [KeyboardButton("✅ Отметить выполнение"), KeyboardButton("🔥 Мой стрик")],
            [KeyboardButton("🧴 Мои продукты"), KeyboardButton("🔍 Сканер состава")],
            [KeyboardButton("👯 Друзья"), KeyboardButton("⚙️ Настройки")],
        ],
        resize_keyboard=True,
        persistent=True,
    )


# ── Onboarding ────────────────────────────────────────────────────────────────

def start_onboarding_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Начать анализ", callback_data="onboarding:start")]
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
    rows.append([
        InlineKeyboardButton("➡️ Готово", callback_data="problems:done"),
    ])
    return InlineKeyboardMarkup(rows)


def budget_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Бюджетный", callback_data="budget:low")],
        [InlineKeyboardButton("💳 Средний", callback_data="budget:medium")],
        [InlineKeyboardButton("💎 Премиум", callback_data="budget:high")],
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


# ── Tracking ──────────────────────────────────────────────────────────────────

def tracking_keyboard(morning_done: bool, evening_done: bool) -> InlineKeyboardMarkup:
    morning_icon = "✅" if morning_done else "☐"
    evening_icon = "✅" if evening_done else "☐"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{morning_icon} Утро", callback_data="track:morning"),
            InlineKeyboardButton(f"{evening_icon} Вечер", callback_data="track:evening"),
        ],
        [InlineKeyboardButton("💾 Сохранить", callback_data="track:save")],
    ])


def reminder_done_keyboard(period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"✅ Отметить {'утреннюю' if period == 'morning' else 'вечернюю'} рутину выполненной",
            callback_data=f"quick_track:{period}"
        )]
    ])


# ── Products ──────────────────────────────────────────────────────────────────

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
    ])


def product_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌅 Утро", callback_data="ptime:morning"),
            InlineKeyboardButton("🌙 Вечер", callback_data="ptime:evening"),
            InlineKeyboardButton("🔄 Оба", callback_data="ptime:both"),
        ]
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


# ── Scanner ───────────────────────────────────────────────────────────────────

def scanner_result_keyboard(wb_url: str = None, za_url: str = None) -> InlineKeyboardMarkup:
    rows = []
    if wb_url:
        rows.append([InlineKeyboardButton("🛒 Найти на WB", url=wb_url)])
    if za_url:
        rows.append([InlineKeyboardButton("🛒 Найти на ЗЯ", url=za_url)])
    rows.append([InlineKeyboardButton("🔍 Сканировать ещё", callback_data="scanner:new")])
    return InlineKeyboardMarkup(rows)


def scan_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Ввести название", callback_data="scan:by_name")],
        [InlineKeyboardButton("📷 Сфотографировать состав", callback_data="scan:by_photo")],
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
        ("🇺🇦 Киев (UTC+2)", "Europe/Kiev"),
        ("🇰🇿 Алматы (UTC+6)", "Asia/Almaty"),
    ]
    rows = [[InlineKeyboardButton(label, callback_data=f"tz:{tz}")] for label, tz in timezones]
    return InlineKeyboardMarkup(rows)


# ── Friends ───────────────────────────────────────────────────────────────────

def friends_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Поделиться ссылкой", switch_inline_query=referral_link)],
    ])
