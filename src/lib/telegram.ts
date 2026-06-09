import {
  backButton,
  hapticFeedback,
  init,
  initData,
  isTMA,
  mainButton,
  miniApp,
  retrieveRawInitData,
  swipeBehavior,
  themeParams,
  viewport,
  type ImpactHapticFeedbackStyle,
} from '@telegram-apps/sdk-react';

let insideTelegram = false;

/**
 * Инициализирует Telegram SDK и монтирует компоненты.
 * Вызывается один раз до рендера приложения.
 * Вне Telegram (обычный браузер) возвращает false — приложение
 * покажет экран «Откройте через Telegram».
 */
export function initTelegram(): boolean {
  if (!isTMA()) {
    insideTelegram = false;
    return false;
  }

  init();

  if (themeParams.mountSync.isAvailable()) themeParams.mountSync();
  if (miniApp.mountSync.isAvailable()) miniApp.mountSync();
  initData.restore();
  if (backButton.mount.isAvailable()) backButton.mount();
  if (mainButton.mount.isAvailable()) mainButton.mount();

  if (swipeBehavior.mount.isAvailable()) {
    swipeBehavior.mount();
    if (swipeBehavior.disableVertical.isAvailable()) {
      swipeBehavior.disableVertical();
    }
  }

  if (viewport.mount.isAvailable()) {
    void viewport.mount().then(() => {
      if (viewport.expand.isAvailable()) viewport.expand();
    });
  }

  if (miniApp.ready.isAvailable()) miniApp.ready();

  insideTelegram = true;
  return true;
}

export function isInsideTelegram(): boolean {
  return insideTelegram;
}

/** Сырая строка initData для серверной валидации. */
export function getRawInitData(): string | undefined {
  if (!insideTelegram) return undefined;
  try {
    return retrieveRawInitData();
  } catch {
    return undefined;
  }
}

/** Синхронизирует цвета шапки и фона Telegram с темой приложения. */
export function syncChromeColors(isDark: boolean) {
  if (!insideTelegram) return;
  const bg = isDark ? '#161412' : '#F7F2EB';
  if (miniApp.setHeaderColor.isAvailable()) miniApp.setHeaderColor(bg);
  if (miniApp.setBackgroundColor.isAvailable()) miniApp.setBackgroundColor(bg);
  if (miniApp.setBottomBarColor.isAvailable()) miniApp.setBottomBarColor(bg);
}

export const haptics = {
  impact(style: ImpactHapticFeedbackStyle = 'light') {
    if (hapticFeedback.impactOccurred.isAvailable()) {
      hapticFeedback.impactOccurred(style);
    }
  },
  success() {
    if (hapticFeedback.notificationOccurred.isAvailable()) {
      hapticFeedback.notificationOccurred('success');
    }
  },
  error() {
    if (hapticFeedback.notificationOccurred.isAvailable()) {
      hapticFeedback.notificationOccurred('error');
    }
  },
  selection() {
    if (hapticFeedback.selectionChanged.isAvailable()) {
      hapticFeedback.selectionChanged();
    }
  },
};
