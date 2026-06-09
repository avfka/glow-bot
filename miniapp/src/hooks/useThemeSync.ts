import { miniApp, useSignal } from '@telegram-apps/sdk-react';
import { useEffect } from 'react';

import { isInsideTelegram, syncChromeColors } from '@/lib/telegram';

function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle('dark', dark);
  syncChromeColors(dark);
}

/**
 * Держит класс `dark` на <html> в синхроне с темой Telegram.
 * Вне Telegram использует prefers-color-scheme.
 */
export function useThemeSync() {
  const tgDark = useSignal(miniApp.isDark);

  useEffect(() => {
    if (isInsideTelegram()) {
      applyTheme(tgDark);
      return;
    }
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    applyTheme(mq.matches);
    const onChange = (e: MediaQueryListEvent) => applyTheme(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [tgDark]);
}
