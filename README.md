# Glow Studio ✨

**Telegram Mini App — операционная система для косметолога.**
Клиенты, записи, услуги и AI-разбор составов косметики — в одном приложении внутри Telegram.

## Возможности

- 📋 **Клиенты** — карточки с контактами, типом кожи, аллергиями и противопоказаниями, заметками, историей процедур и фото «до/после» (приватное хранилище)
- 📅 **Записи** — календарь в режимах «день/неделя», статусы, напоминания в Telegram
- 💅 **Услуги** — каталог процедур с ценами и длительностью
- 🧪 **AI-разбор составов** — вставьте INCI-список или сфотографируйте этикетку: приложение вернёт структурированный разбор (назначение компонентов, раздражители и аллергены, комедогенность, предупреждения по типам кожи, несовместимости активов)
- 📊 **Дашборд** — записи на сегодня, ближайшие, мини-статистика и анимированная иллюстрация
- 🎨 Полная поддержка светлой/тёмной темы Telegram, нативные BackButton/MainButton, haptic feedback

## Стек

| Слой | Технологии |
|---|---|
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · shadcn/ui (Radix) · framer-motion |
| Telegram | @telegram-apps/sdk-react (theme params, viewport, MainButton, haptics, initData) |
| Данные | TanStack Query · Zustand · React Router |
| Backend | Supabase: Postgres + RLS, Auth, Storage, Edge Functions (Deno) |
| AI | Anthropic API, `claude-sonnet-4-6` + structured outputs |

## Архитектура

```
Telegram Mini App ── initData ──► Edge Function telegram-auth
                                    │ HMAC-валидация подписи токеном бота,
                                    │ upsert специалиста, выдача сессии
                                    ▼
                    Supabase (Postgres + RLS + Storage)
                                    ▲
Edge Function analyze-ingredients ──┘──► Anthropic API (строгий JSON)
Edge Function send-reminders (cron) ───► Telegram Bot API
```

**Безопасность:** RLS включён на всех таблицах — специалист видит только своих клиентов и записи. Фото клиентов лежат в приватном бакете, доступ по signed URL и политикам `storage.objects`. Ключ Anthropic и токен бота существуют только в секретах Edge Functions.

## Структура

```
src/
├── app/            # роутер, AppShell, таббар, AuthGate
├── components/
│   ├── ui/         # UI-кит (shadcn-стиль на дизайн-токенах)
│   └── shared/     # EmptyState, PageHeader, скелетоны
├── features/
│   ├── dashboard/  # главный экран + анимированный hero
│   ├── appointments/
│   ├── clients/
│   ├── services/
│   ├── analyzer/   # AI-разбор составов
│   └── onboarding/
├── hooks/          # useMainButton, useBackButton, useThemeSync
├── lib/            # supabase, telegram, format
├── stores/         # zustand: сессия
└── types/          # типы схемы БД + доменные

supabase/
├── migrations/     # SQL-схема + RLS + storage-политики
└── functions/      # telegram-auth, analyze-ingredients, send-reminders
```

## Запуск

### 1. Бот и Mini App в BotFather

1. Создайте бота: `@BotFather` → `/newbot`, сохраните токен.
2. После деплоя фронтенда: `/newapp` → укажите URL приложения. Для кнопки меню: `/setmenubutton`.

### 2. Supabase

```bash
npm i -g supabase
supabase login

# создайте проект на supabase.com, затем:
supabase link --project-ref <project-ref>

# применить миграции (схема + RLS + storage)
supabase db push

# секреты edge functions
supabase secrets set TELEGRAM_BOT_TOKEN=123456:ABC-...
supabase secrets set ANTHROPIC_API_KEY=sk-ant-...
supabase secrets set AUTH_PEPPER=$(openssl rand -hex 32)

# деплой функций
supabase functions deploy telegram-auth
supabase functions deploy analyze-ingredients
supabase functions deploy send-reminders
```

### 3. Напоминания (cron)

В SQL-редакторе Supabase включите расширения `pg_cron` и `pg_net`, затем:

```sql
select cron.schedule(
  'send-reminders',
  '*/10 * * * *',
  $$
  select net.http_post(
    url := 'https://<project-ref>.supabase.co/functions/v1/send-reminders',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer <service-role-key>'
    ),
    body := '{}'::jsonb
  );
  $$
);
```

### 4. Frontend

```bash
cp .env.example .env   # заполните VITE_SUPABASE_URL и VITE_SUPABASE_ANON_KEY
npm install
npm run dev            # локальная разработка
npm run build          # production-сборка в dist/
```

Деплойте `dist/` на любой статический хостинг с HTTPS (Vercel, Netlify, Cloudflare Pages) и укажите URL в BotFather. Роутинг — hash-based, SPA-rewrite не требуется.

> Вне Telegram приложение показывает заглушку «Откройте через Telegram»: авторизация требует подписанный `initData`.

### Обновление типов БД

После изменения миграций:

```bash
supabase gen types typescript --linked > src/types/database.ts
```

## Дисклеймер

AI-разбор составов носит справочный характер и не является медицинским заключением. Финальное решение — за специалистом.
