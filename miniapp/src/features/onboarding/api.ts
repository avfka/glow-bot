import { useMutation } from '@tanstack/react-query';

import { supabase } from '@/lib/supabase';
import { haptics } from '@/lib/telegram';
import { useSession } from '@/stores/session';
import type { Database } from '@/types/database';

type SpecialistUpdate = Database['public']['Tables']['specialists']['Update'];

export function useUpdateSpecialist() {
  const setSpecialist = useSession((s) => s.setSpecialist);

  return useMutation({
    mutationFn: async (patch: SpecialistUpdate) => {
      const { data: userData } = await supabase.auth.getUser();
      if (!userData.user) throw new Error('Сессия недействительна');

      const { data, error } = await supabase
        .from('specialists')
        .update(patch)
        .eq('id', userData.user.id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: (specialist) => {
      setSpecialist(specialist);
      haptics.success();
    },
    onError: () => haptics.error(),
  });
}
