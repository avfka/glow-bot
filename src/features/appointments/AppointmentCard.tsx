import { Link } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { formatDuration, formatPrice, formatTime } from '@/lib/format';
import { haptics } from '@/lib/telegram';
import type { AppointmentStatus } from '@/types/database';
import { APPOINTMENT_STATUS_LABELS, type AppointmentWithRelations } from '@/types/domain';

const STATUS_VARIANT: Record<AppointmentStatus, 'secondary' | 'success' | 'outline' | 'destructive'> = {
  scheduled: 'secondary',
  done: 'success',
  cancelled: 'outline',
  no_show: 'destructive',
};

export function AppointmentCard({ appointment }: { appointment: AppointmentWithRelations }) {
  const muted = appointment.status === 'cancelled' || appointment.status === 'no_show';

  return (
    <Link
      to={`/appointments/${appointment.id}/edit`}
      onClick={() => haptics.selection()}
      className={`flex items-center gap-4 rounded-2xl bg-card p-4 shadow-soft transition-transform active:scale-[0.99] ${muted ? 'opacity-55' : ''}`}
    >
      <div className="flex w-[52px] shrink-0 flex-col items-center rounded-xl bg-accent py-2">
        <span className="text-[15px] font-semibold leading-none text-accent-foreground">
          {formatTime(appointment.starts_at)}
        </span>
        <span className="mt-1 text-[11px] leading-none text-accent-foreground/70">
          {formatDuration(appointment.duration_min)}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[15px] font-medium">
          {appointment.client?.name ?? 'Клиент удалён'}
        </div>
        <div className="mt-0.5 truncate text-[13px] text-muted-foreground">
          {appointment.service?.name ?? 'Без услуги'}
          {appointment.price > 0 ? ` · ${formatPrice(appointment.price)}` : ''}
        </div>
      </div>
      <Badge variant={STATUS_VARIANT[appointment.status]} className="shrink-0">
        {APPOINTMENT_STATUS_LABELS[appointment.status]}
      </Badge>
    </Link>
  );
}
