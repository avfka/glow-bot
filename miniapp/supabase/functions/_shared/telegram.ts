/**
 * Валидация Telegram Mini App initData.
 * https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
 */

const encoder = new TextEncoder();

async function hmacSha256(key: ArrayBuffer | Uint8Array, message: string): Promise<ArrayBuffer> {
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    key as ArrayBuffer,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  return crypto.subtle.sign('HMAC', cryptoKey, encoder.encode(message));
}

function toHex(buffer: ArrayBuffer): string {
  return [...new Uint8Array(buffer)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
}

const MAX_INIT_DATA_AGE_SEC = 24 * 60 * 60;

/**
 * Проверяет подпись initData и возвращает пользователя Telegram.
 * Бросает ошибку, если подпись неверна или данные устарели.
 */
export async function validateInitData(initData: string, botToken: string): Promise<TelegramUser> {
  const params = new URLSearchParams(initData);
  const hash = params.get('hash');
  if (!hash) throw new Error('initData не содержит hash');

  params.delete('hash');
  const dataCheckString = [...params.entries()]
    .map(([key, value]) => `${key}=${value}`)
    .sort()
    .join('\n');

  // secret_key = HMAC_SHA256(bot_token, key="WebAppData")
  const secretKey = await hmacSha256(encoder.encode('WebAppData'), botToken);
  const computedHash = toHex(await hmacSha256(secretKey, dataCheckString));

  if (computedHash !== hash) throw new Error('Неверная подпись initData');

  const authDate = Number(params.get('auth_date') ?? 0);
  if (!authDate || Date.now() / 1000 - authDate > MAX_INIT_DATA_AGE_SEC) {
    throw new Error('initData устарела, переоткройте приложение');
  }

  const userRaw = params.get('user');
  if (!userRaw) throw new Error('initData не содержит пользователя');

  return JSON.parse(userRaw) as TelegramUser;
}

/** Детерминированный пароль auth-пользователя: HMAC от telegram_id с серверным секретом. */
export async function derivePassword(telegramId: number, pepper: string): Promise<string> {
  return toHex(await hmacSha256(encoder.encode(pepper), `tg:${telegramId}`));
}
