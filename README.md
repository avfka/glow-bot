# GlowBot — AI-косметолог 🌸

Telegram-бот с персональной рутиной ухода за кожей на основе AI-анализа.

## Возможности

- 📸 Анализ кожи по фото (OpenAI Vision)
- 🧴 Персональная утренняя и вечерняя рутина
- ✅ Трекер выполнения рутины и стрики
- 🔍 Сканер состава косметики (OCR + оценка)
- ⏰ Напоминания с учётом часового пояса
- 👯 Соревнование со стриками среди друзей
- 🔄 Версионирование всех данных — история изменений без потерь

## Стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11 |
| Telegram Bot | python-telegram-bot v20+ |
| База данных | PostgreSQL (asyncpg + SQLAlchemy async) |
| AI анализ | OpenAI gpt-4o-mini (заменяемо) |
| Напоминания | APScheduler AsyncIOScheduler |
| Деплой | Railway |

## Локальный запуск

### 1. Клонировать и установить зависимости

```bash
git clone <repo>
cd glow-bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Заполнить переменные:

```env
TELEGRAM_BOT_TOKEN=токен_от_BotFather
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/glowbot
WEBHOOK_URL=  # пустое = polling режим
```

`postgresql://...` и `postgres://...` тоже поддерживаются — приложение нормализует URL к asyncpg-драйверу.

### 3. Создать базу данных и применить миграции

```bash
createdb glowbot
alembic upgrade head
```

Схема базы управляется через Alembic-миграции.

Если база уже была создана старой версией бота через `create_all`, сначала проверь схему и пометь текущую ревизию:

```bash
alembic stamp head
```

### 4. Запустить

```bash
python bot.py
```

## Деплой на Railway

### 1. Создать проект

```bash
railway new
railway link
```

### 2. Добавить PostgreSQL

В панели Railway: New → Database → PostgreSQL.

### 3. Переменные окружения

В Railway Dashboard → Variables:

```
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
DATABASE_URL=${{Postgres.DATABASE_URL}}  # авто из Railway
WEBHOOK_URL=https://<твой-домен>.railway.app
PORT=8000
```

### 4. Деплой

```bash
railway up
```

Railway автоматически выполнит `alembic upgrade head && python bot.py` из Dockerfile.

## Архитектура

### Версионирование данных

Данные **никогда не удаляются и не перезаписываются**.
Каждое изменение = новая запись с `created_at`.
Актуальная версия = последняя по `created_at`.

```
user_profile_versions  ← история профиля кожи
routines               ← история рутин
skin_analysis_history  ← история анализов
```

### Замена AI-движка

Текущая реализация: `services/openai_service.py`
Абстрактный интерфейс: `services/skin_analyzer.py`
Будущий движок: `services/ml_engine.py`

Для переключения — одна строка в `.env`:
```env
SKIN_ANALYZER_BACKEND=ml_engine
```

### Структура проекта

```
glowbot/
├── bot.py                  # точка входа
├── config.py               # настройки (pydantic-settings)
├── scheduler.py            # APScheduler напоминания
├── database/
│   ├── __init__.py         # движок + фабрика сессий
│   ├── models.py           # SQLAlchemy ORM модели
│   └── queries.py          # async CRUD функции
├── handlers/
│   ├── onboarding.py       # /start + онбординг флоу
│   ├── tracking.py         # /track, /streak
│   ├── products.py         # /products
│   ├── scanner.py          # /scan — сканер состава
│   ├── friends.py          # /friends, /leaderboard
│   └── settings.py        # /settings
├── services/
│   ├── skin_analyzer.py    # абстрактный класс
│   ├── openai_service.py   # OpenAI реализация
│   ├── ml_engine.py        # заглушка ML движка
│   └── ingredient_scorer.py # оценка состава
└── utils/
    └── keyboards.py        # все клавиатуры
```

## Команды бота

| Команда | Описание |
|---------|---------|
| `/start` | Онбординг или главное меню |
| `/routine` | Текущая рутина |
| `/track` | Отметить выполнение |
| `/streak` | Текущий стрик |
| `/products` | Управление продуктами |
| `/scan` | Сканер состава |
| `/friends` | Реферальная программа |
| `/settings` | Настройки напоминаний |

## Дисклеймер

Анализ носит рекомендательный характер и не является медицинским заключением.
При серьёзных проблемах кожи обратитесь к дерматологу.
