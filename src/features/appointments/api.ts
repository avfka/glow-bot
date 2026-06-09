import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { supabase } from '@/lib/supabase';
import { haptics } from '@/lib/telegram';
import { useSession } from '@/stores/session';
import type { Database } from '@/types/database';

type AppointmentInsert = Database['public']['Tables']['appointments']['Insert'];
type AppointmentUpdate = Database['public']['Tables']['appointments']['Update'];

export const appointmentsKey = ['appointments'] as const;

const APPOINTMENT_WITH_RELATIONS = '*, client:clients(id, name), service:services(id, name)';

/** Записи в интервале [from, to) с клиентом и услугой. */
export function useAppointmentsRange(fromISO: string, toISO: string) {
  return useQuery({
    queryKey: [...appointmentsKey, { from: fromISO, to: toISO }],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('appointments')
        .select(APPOINTMENT_WITH_RELATIONS)
        .gte('starts_at', fromISO)
        .lt('starts_at', toISO)
        .order('starts_at');
      if (error) throw error;
      return data;
    },
    placeholderData: (prev) => prev,
  });
}

export function useAppointment(id: string | undefined) {
  return useQuery({
    queryKey: [...appointmentsKey, id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('appointments')
        .select(APPOINTMENT_WITH_RELATIONS)
        .eq('id', id!)
        .single();
      if (error) throw error;
      return data;
    },
  });
}

function useInvalidateAppointments() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: appointmentsKey });
}

export function useCreateAppointment() {
  const invalidate = useInvalidateAppointments();
  const specialistId = useSession((s) => s.specialist?.id);

  return useMutation({
    mutationFn: async (input: Omit<AppointmentInsert, 'specialist_id'>) => {
      if (!specialistId) throw new Error('Сессия недействительна');
      const { data, error } = await supabase
        .from('appointments')
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

export function useUpdateAppointment() {
  const invalidate = useInvalidateAppointments();

  return useMutation({
    mutationFn: async ({ id, ...patch }: AppointmentUpdate & { id: string }) => {
      const { data, error } = await supabase
        .from('appointments')
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

export function useDeleteAppointment() {
  const invalidate = useInvalidateAppointments();

  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from('appointments').delete().eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => {
      haptics.success();
      void invalidate();
    },
    onError: () => haptics.error(),
  });
}
