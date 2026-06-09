/**
 * Авторизация Telegram Mini App.
 *
 * Принимает initData, проверяет HMAC-подпись токеном бота, создаёт (при первом
 * входе) auth-пользователя и строку специалиста, возвращает Supabase-сессию.
 */
import { createClient } from 'npm:@supabase/supabase-js@2';

import { corsHeaders, jsonResponse } from '../_shared/cors.ts';
import { derivePassword, validateInitData } from '../_shared/telegram.ts';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const BOT_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN');
const AUTH_PEPPER = Deno.env.get('AUTH_PEPPER');

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return jsonResponse({ error: 'Метод не поддерживается' }, 405);
  }
  if (!BOT_TOKEN || !AUTH_PEPPER) {
    return jsonResponse({ error: 'Функция не сконфигурирована: TELEGRAM_BOT_TOKEN / AUTH_PEPPER' }, 500);
  }

  try {
    const { initData } = (await req.json()) as { initData?: string };
    if (!initData) return jsonResponse({ error: 'initData обязателен' }, 400);

    const tgUser = await validateInitData(initData, BOT_TOKEN);

    const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    const email = `tg-${tgUser.id}@glow-studio.app`;
    const password = await derivePassword(tgUser.id, AUTH_PEPPER);

    let session = (await admin.auth.signInWithPassword({ email, password })).data.session;

    if (!session) {
      // Первый вход: создаём auth-пользователя и профиль специалиста
      const { data: created, error: createError } = await admin.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        app_metadata: { telegram_id: tgUser.id },
      });
      if (createError) throw createError;

      const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ');
      const { error: insertError } = await admin.from('specialists').insert({
        id: created.user.id,
        telegram_id: tgUser.id,
        name: fullName,
        avatar_url: tgUser.photo_url ?? null,
      });
      if (insertError && insertError.code !== '23505') throw insertError;

      const retry = await admin.auth.signInWithPassword({ email, password });
      if (retry.error) throw retry.error;
      session = retry.data.session;
    }

    if (!session) throw new Error('Не удалось создать сессию');

    return jsonResponse({
      access_token: session.access_token,
      refresh_token: session.refresh_token,
    });
  } catch (error) {
    console.error('telegram-auth error:', error);
    const message = error instanceof Error ? error.message : 'Ошибка авторизации';
    return jsonResponse({ error: message }, 401);
  }
});
