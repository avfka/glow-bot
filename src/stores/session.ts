import { create } from 'zustand';

import { callEdgeFunction, supabase } from '@/lib/supabase';
import { getRawInitData } from '@/lib/telegram';
import type { Specialist } from '@/types/domain';

type SessionStatus = 'loading' | 'ready' | 'error';

interface SessionState {
  status: SessionStatus;
  specialist: Specialist | null;
  error: string | null;
  authenticate: () => Promise<void>;
  setSpecialist: (specialist: Specialist) => void;
}

async function fetchSpecialist(): Promise<Specialist> {
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData.user) throw new Error('Сессия недействительна');

  const { data, error } = await supabase
    .from('specialists')
    .select('*')
    .eq('id', userData.user.id)
    .single();
  if (error) throw new Error('Профиль специалиста не найден');
  return data;
}

export const useSession = create<SessionState>((set) => ({
  status: 'loading',
  specialist: null,
  error: null,

  authenticate: async () => {
    set({ status: 'loading', error: null });
    try {
      const { data } = await supabase.auth.getSession();

      if (!data.session) {
        const initData = getRawInitData();
        if (!initData) throw new Error('Не удалось получить данные Telegram');

        const tokens = await callEdgeFunction<{ access_token: string; refresh_token: string }>(
          'telegram-auth',
          { initData },
        );
        const { error } = await supabase.auth.setSession(tokens);
        if (error) throw error;
      }

      const specialist = await fetchSpecialist();
      set({ status: 'ready', specialist });
    } catch (e) {
      set({ status: 'error', error: e instanceof Error ? e.message : 'Ошибка авторизации' });
    }
  },

  setSpecialist: (specialist) => set({ specialist }),
}));
