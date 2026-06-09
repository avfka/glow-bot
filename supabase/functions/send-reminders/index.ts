/**
 * Напоминания о записях.
 *
 * Вызывается по расписанию (pg_cron + pg_net, см. README). Находит записи,
 * у которых наступило окно напоминания, и отправляет специалисту сообщение
 * в Telegram через Bot API. Повторная отправка исключена полем reminded_at.
 */
import { createClient } from 'npm:@supabase/supabase-js@2';

import { jsonResponse } from '../_shared/cors.ts';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const BOT_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN');

interface ReminderRow {
  id: string;
  starts_at: string;
  remind_before_min: number;
  specialist: { telegram_id: number } | null;
  client: { name: string } | null;
  service: { name: string } | null;
}

function formatStartsAt(iso: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Moscow',
  }).format(new Date(iso));
}

Deno.serve(async (req) => {
  // Функция вызывается только инфраструктурой — требуем service role key
  if (req.headers.get('Authorization') !== `Bearer ${SERVICE_ROLE_KEY}`) {
    return jsonResponse({ error: 'Недостаточно прав' }, 401);
  }
  if (!BOT_TOKEN) {
    return jsonResponse({ error: 'TELEGRAM_BOT_TOKEN не задан' }, 500);
  }

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const now = Date.now();
  const horizon = new Date(now + 24 * 60 * 60 * 1000).toISOString();

  const { data, error } = await admin
    .from('appointments')
    .select(
      'id, starts_at, remind_before_min, specialist:specialists(telegram_id), client:clients(name), service:services(name)',
    )
    .eq('status', 'scheduled')
    .is('reminded_at', null)
    .not('remind_before_min', 'is', null)
    .gt('starts_at', new Date(now).toISOString())
    .lte('starts_at', horizon);

  if (error) {
    console.error('send-reminders query error:', error);
    return jsonResponse({ error: error.message }, 500);
  }

  const due = (data as unknown as ReminderRow[]).filter(
    (row) => new Date(row.starts_at).getTime() - row.remind_before_min * 60_000 <= now,
  );

  let sent = 0;
  for (const row of due) {
    if (!row.specialist?.telegram_id) continue;

    const text = [
      '⏰ Скоро запись',
      `${formatStartsAt(row.starts_at)} — ${row.client?.name ?? 'клиент'}`,
      row.service?.name ?? '',
    ]
      .filter(Boolean)
      .join('\n');

    const response = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: row.specialist.telegram_id, text }),
    });

    if (response.ok) {
      await admin
        .from('appointments')
        .update({ reminded_at: new Date().toISOString() })
        .eq('id', row.id);
      sent += 1;
    } else {
      console.error('sendMessage failed:', row.id, await response.text());
    }
  }

  return jsonResponse({ checked: due.length, sent });
});
