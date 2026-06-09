import type { AppointmentStatus, Database, SkinType } from './database';

export type Specialist = Database['public']['Tables']['specialists']['Row'];
export type Client = Database['public']['Tables']['clients']['Row'];
export type Service = Database['public']['Tables']['services']['Row'];
export type Appointment = Database['public']['Tables']['appointments']['Row'];
export type ClientPhoto = Database['public']['Tables']['client_photos']['Row'];
export type IngredientAnalysis = Database['public']['Tables']['ingredient_analyses']['Row'];

/** Запись с подтянутыми клиентом и услугой (для списков и карточек). */
export type AppointmentWithRelations = Appointment & {
  client: Pick<Client, 'id' | 'name'> | null;
  service: Pick<Service, 'id' | 'name'> | null;
};

export const SKIN_TYPE_LABELS: Record<SkinType, string> = {
  normal: 'Нормальная',
  dry: 'Сухая',
  oily: 'Жирная',
  combination: 'Комбинированная',
  sensitive: 'Чувствительная',
};

export const APPOINTMENT_STATUS_LABELS: Record<AppointmentStatus, string> = {
  scheduled: 'Запланирована',
  done: 'Выполнена',
  cancelled: 'Отменена',
  no_show: 'Неявка',
};
