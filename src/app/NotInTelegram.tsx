import { Send } from 'lucide-react';

export function NotInTelegram() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-8 text-center">
      <div className="mb-6 flex size-16 items-center justify-center rounded-full bg-accent">
        <Send className="size-7 text-accent-foreground" strokeWidth={1.6} />
      </div>
      <h1 className="text-xl font-semibold tracking-tight">Glow Studio</h1>
      <p className="mt-2 max-w-[280px] text-sm leading-relaxed text-muted-foreground">
        Это Telegram Mini App. Откройте приложение через вашего бота в Telegram, чтобы продолжить.
      </p>
    </div>
  );
}
