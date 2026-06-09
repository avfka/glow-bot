import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { supabase } from '@/lib/supabase';
import { haptics } from '@/lib/telegram';
import { useSession } from '@/stores/session';
import type { Database } from '@/types/database';

type ServiceInsert = Database['public']['Tables']['services']['Insert'];
type ServiceUpdate = Database['public']['Tables']['services']['Update'];

const servicesKey = ['services'] as const;

export function useServices() {
  return useQuery({
    queryKey: servicesKey,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('services')
        .select('*')
        .order('is_active', { ascending: false })
        .order('name');
      if (error) throw error;
      return data;
    },
  });
}

function useInvalidateServices() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: servicesKey });
}

export function useCreateService() {
  const invalidate = useInvalidateServices();
  const specialistId = useSession((s) => s.specialist?.id);

  return useMutation({
    mutationFn: async (input: Omit<ServiceInsert, 'specialist_id'>) => {
      if (!specialistId) throw new Error('Сессия недействительна');
      const { data, error } = await supabase
        .from('services')
        .insert({ ...input, specialist_id: specialistId })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      haptics.success();
      void invalidate();
    },
    onError: () => haptics.error(),
  });
}

export function useUpdateService() {
  const invalidate = useInvalidateServices();

  return useMutation({
    mutationFn: async ({ id, ...patch }: ServiceUpdate & { id: string }) => {
      const { data, error } = await supabase
        .from('services')
        .update(patch)
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      haptics.success();
      void invalidate();
    },
    onError: () => haptics.error(),
  });
}

export function useDeleteService() {
  const invalidate = useInvalidateServices();

  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from('services').delete().eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => {
      haptics.success();
      void invalidate();
    },
    onError: () => haptics.error(),
  });
}
