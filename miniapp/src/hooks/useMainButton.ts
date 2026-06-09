import { mainButton } from '@telegram-apps/sdk-react';
import { useEffect, useRef } from 'react';

import { isInsideTelegram } from '@/lib/telegram';

interface MainButtonOptions {
  text: string;
  onClick: () => void;
  /** Показывать ли кнопку. По умолчанию true. */
  visible?: boolean;
  enabled?: boolean;
  loading?: boolean;
}

function brandColors() {
  const dark = document.documentElement.classList.contains('dark');
  return dark
    ? { backgroundColor: '#CDA89A' as const, textColor: '#221B17' as const }
    : { backgroundColor: '#BC8F7F' as const, textColor: '#FFF8F4' as const };
}

/**
 * Декларативное управление нативной MainButton Telegram.
 * Кнопка скрывается при размонтировании экрана.
 */
export function useMainButton({ text, onClick, visible = true, enabled = true, loading = false }: MainButtonOptions) {
  const handlerRef = useRef(onClick);
  handlerRef.current = onClick;

  useEffect(() => {
    if (!isInsideTelegram() || !mainButton.setParams.isAvailable()) return;
    mainButton.setParams({
      text,
      isVisible: visible,
      isEnabled: enabled && !loading,
      isLoaderVisible: loading,
      hasShineEffect: false,
      ...brandColors(),
    });
  }, [text, visible, enabled, loading]);

  useEffect(() => {
    if (!isInsideTelegram()) return;
    const handler = () => handlerRef.current();
    if (mainButton.onClick.isAvailable()) mainButton.onClick(handler);
    return () => {
      if (mainButton.offClick.isAvailable()) mainButton.offClick(handler);
      if (mainButton.setParams.isAvailable()) {
        mainButton.setParams({ isVisible: false, isLoaderVisible: false });
      }
    };
  }, []);
}
