import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { supabase } from '@/lib/supabase';
import { haptics } from '@/lib/telegram';
import { useSession } from '@/stores/session';
import type { Database, PhotoKind } from '@/types/database';
import type { ClientPhoto } from '@/types/domain';

type ClientInsert = Database['public']['Tables']['clients']['Insert'];
type ClientUpdate = Database['public']['Tables']['clients']['Update'];

export const clientsKey = ['clients'] as const;

export function useClients(search: string) {
  const term = search.trim();
  return useQuery({
    queryKey: [...clientsKey, { search: term }],
    queryFn: async () => {
      let query = supabase.from('clients').select('*').order('name');
      if (term) {
        query = query.or(`name.ilike.%${term}%,phone.ilike.%${term}%`);
      }
      const { data, error } = await query;
      if (error) throw error;
      return data;
    },
    placeholderData: (prev) => prev,
  });
}

export function useClient(id: string | undefined) {
  return useQuery({
    queryKey: [...clientsKey, id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data, error } = await supabase.from('clients').select('*').eq('id', id!).single();
      if (error) throw error;
      return data;
    },
  });
}

export function useCreateClient() {
  const queryClient = useQueryClient();
  const specialistId = useSession((s) => s.specialist?.id);

  return useMutation({
    mutationFn: async (input: Omit<ClientInsert, 'specialist_id'>) => {
      if (!specialistId) throw new Error('Сессия недействительна');
      const { data, error } = await supabase
        .from('clients')
        .insert({ ...input, specialist_id: specialistId })
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: clientsKey });
    },
    onError: () => haptics.error(),
  });
}

export function useUpdateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...patch }: ClientUpdate & { id: string }) => {
      const { data, error } = await supabase
        .from('clients')
        .update(patch)
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: clientsKey });
    },
    onError: () => haptics.error(),
  });
}

export function useDeleteClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from('clients').delete().eq('id', id);
      if (error) throw error;
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: clientsKey });
    },
    onError: () => haptics.error(),
  });
}

/** История процедур клиента (записи с услугой, новые сверху). */
export function useClientAppointments(clientId: string | undefined) {
  return useQuery({
    queryKey: ['appointments', { clientId }],
    enabled: Boolean(clientId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('appointments')
        .select('*, service:services(id, name)')
        .eq('client_id', clientId!)
        .order('starts_at', { ascending: false });
      if (error) throw error;
      return data;
    },
  });
}

export type ClientPhotoWithUrl = ClientPhoto & { url: string };

export function useClientPhotos(clientId: string | undefined) {
  return useQuery({
    queryKey: ['client-photos', clientId],
    enabled: Boolean(clientId),
    queryFn: async (): Promise<ClientPhotoWithUrl[]> => {
      const { data: photos, error } = await supabase
        .from('client_photos')
        .select('*')
        .eq('client_id', clientId!)
        .order('created_at', { ascending: false });
      if (error) throw error;
      if (photos.length === 0) return [];

      const { data: signed, error: signError } = await supabase.storage
        .from('client-photos')
        .createSignedUrls(
          photos.map((p) => p.storage_path),
          60 * 60,
        );
      if (signError) throw signError;

      return photos.map((photo, i) => ({ ...photo, url: signed[i]?.signedUrl ?? '' }));
    },
  });
}

export function useUploadClientPhoto(clientId: string) {
  const queryClient = useQueryClient();
  const specialistId = useSession((s) => s.specialist?.id);

  return useMutation({
    mutationFn: async ({ file, kind }: { file: File; kind: PhotoKind }) => {
      if (!specialistId) throw new Error('Сессия недействительна');

      const extension = file.name.split('.').pop()?.toLowerCase() || 'jpg';
      const path = `${specialistId}/${clientId}/${crypto.randomUUID()}.${extension}`;

      const { error: uploadError } = await supabase.storage
        .from('client-photos')
        .upload(path, file, { contentType: file.type || 'image/jpeg' });
      if (uploadError) throw uploadError;

      const { error } = await supabase.from('client_photos').insert({
        specialist_id: specialistId,
        client_id: clientId,
        kind,
        storage_path: path,
      });
      if (error) throw error;
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: ['client-photos', clientId] });
    },
    onError: () => haptics.error(),
  });
}

export function useDeleteClientPhoto(clientId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (photo: ClientPhoto) => {
      const { error } = await supabase.from('client_photos').delete().eq('id', photo.id);
      if (error) throw error;
      await supabase.storage.from('client-photos').remove([photo.storage_path]);
    },
    onSuccess: () => {
      haptics.success();
      void queryClient.invalidateQueries({ queryKey: ['client-photos', clientId] });
    },
    onError: () => haptics.error(),
  });
}
