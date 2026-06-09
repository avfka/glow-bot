import { format, isToday, isTomorrow, isYesterday } from 'date-fns';
import { ru } from 'date-fns/locale';

const rub = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
});

export function formatPrice(value: number): string {
  return rub.format(value);
}

export function formatTime(date: Date | string): string {
  return format(new Date(date), 'HH:mm');
}

export function formatDay(date: Date | string): string {
  const d = new Date(date);
  if (isToday(d)) return 'Сегодня';
  if (isTomorrow(d)) return 'Завтра';
  if (isYesterday(d)) return 'Вчера';
  return format(d, 'd MMMM', { locale: ru });
}

export function formatDayShort(date: Date | string): string {
  return format(new Date(date), 'd MMM', { locale: ru });
}

export function formatFullDate(date: Date | string): string {
  return format(new Date(date), 'd MMMM yyyy', { locale: ru });
}

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m} мин`;
  if (m === 0) return `${h} ч`;
  return `${h} ч ${m} мин`;
}

/** «5 клиентов», «1 запись» и т.п. */
export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} ${one}`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} ${few}`;
  return `${n} ${many}`;
}
