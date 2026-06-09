import { backButton } from '@telegram-apps/sdk-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { isInsideTelegram } from '@/lib/telegram';

/**
 * Управляет нативной кнопкой «Назад» Telegram:
 * показывает её на вложенных экранах и навигирует назад по истории.
 */
export function useBackButton(visible: boolean) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!isInsideTelegram()) return;
    if (visible) {
      if (backButton.show.isAvailable()) backButton.show();
    } else if (backButton.hide.isAvailable()) {
      backButton.hide();
    }
  }, [visible]);

  useEffect(() => {
    if (!isInsideTelegram() || !backButton.onClick.isAvailable()) return;
    const handler = () => navigate(-1);
    backButton.onClick(handler);
    return () => backButton.offClick(handler);
  }, [navigate]);
}
