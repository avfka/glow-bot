import { motion } from 'framer-motion';
import { AlertTriangle, History, Pencil, Phone, Send, ShieldAlert, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { formatDayShort, formatPrice, formatTime } from '@/lib/format';
import { APPOINTMENT_STATUS_LABELS, SKIN_TYPE_LABELS } from '@/types/domain';

import { useClient, useClientAppointments, useDeleteClient } from './api';
import { PhotoSection } from './PhotoSection';

function clientInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('');
}

function InfoBlock({
  icon: Icon,
  title,
  value,
  tone,
}: {
  icon: typeof AlertTriangle;
  title: string;
  value: string;
  tone?: 'warning';
}) {
  return (
    <Card className={tone === 'warning' ? 'bg-pastel-peach' : undefined}>
      <CardContent className="flex gap-3 p-4">
        <Icon className="mt-0.5 size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.7} />
        <div className="min-w-0">
          <div className="text-[13px] font-medium text-muted-foreground">{title}</div>
          <div className="mt-0.5 whitespace-pre-wrap text-[14px] leading-relaxed">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ClientPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: client, isPending } = useClient(id);
  const { data: history, isPending: historyLoading } = useClientAppointments(id);
  const remove = useDeleteClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (isPending) {
    return <ListSkeleton count={5} itemHeight={88} />;
  }
  if (!client) {
    return <p className="py-16 text-center text-sm text-muted-foreground">Клиент не найден</p>;
  }

  return (
    <div className="space-y-7">
      <motion.header
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="flex items-start gap-4"
      >
        <Avatar className="size-16">
          <AvatarFallback className="text-lg">{clientInitials(client.name)}</AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <h1 className="text-[22px] font-semibold leading-tight tracking-tight">{client.name}</h1>
          {client.skin_type ? (
            <Badge variant="secondary" className="mt-1.5">
              {SKIN_TYPE_LABELS[client.skin_type]} кожа
            </Badge>
          ) : null}
        </div>
        <Button variant="ghost" size="icon-sm" aria-label="Редактировать" asChild>
          <Link to={`/clients/${client.id}/edit`}>
            <Pencil className="size-4" />
          </Link>
        </Button>
      </motion.header>

      {(client.phone || client.telegram_username) && (
        <div className="flex gap-2.5">
          {client.phone ? (
            <Button variant="secondary" className="flex-1" asChild>
              <a href={`tel:${client.phone.replace(/[^+\d]/g, '')}`}>
                <Phone />
                Позвонить
              </a>
            </Button>
          ) : null}
          {client.telegram_username ? (
            <Button variant="secondary" className="flex-1" asChild>
              <a href={`https://t.me/${client.telegram_username}`} target="_blank" rel="noreferrer">
                <Send />
                Написать
              </a>
            </Button>
          ) : null}
        </div>
      )}

      {(client.allergies || client.contraindications || client.notes) && (
        <section className="space-y-2.5">
          {client.allergies ? (
            <InfoBlock icon={AlertTriangle} title="Аллергии" value={client.allergies} tone="warning" />
          ) : null}
          {client.contraindications ? (
            <InfoBlock
              icon={ShieldAlert}
              title="Противопоказания"
              value={client.contraindications}
              tone="warning"
            />
          ) : null}
          {client.notes ? <InfoBlock icon={Pencil} title="Заметки" value={client.notes} /> : null}
        </section>
      )}

      <PhotoSection clientId={client.id} />

      <section>
        <h2 className="mb-3 text-[15px] font-semibold">История процедур</h2>
        {historyLoading ? (
          <ListSkeleton count={3} itemHeight={64} />
        ) : !history || history.length === 0 ? (
          <p className="rounded-2xl bg-secondary/60 px-4 py-5 text-center text-[13px] text-muted-foreground">
            Процедур пока не было. Создайте запись на вкладке «Записи».
          </p>
        ) : (
          <div className="space-y-2.5">
            {history.map((appointment) => (
              <Link
                key={appointment.id}
                to={`/appointments/${appointment.id}/edit`}
                className="flex items-center gap-3.5 rounded-2xl bg-card p-4 shadow-soft"
              >
                <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent">
                  <History className="size-[18px] text-accent-foreground" strokeWidth={1.7} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[14px] font-medium">
                    {appointment.service?.name ?? 'Процедура'}
                  </div>
                  <div className="text-[13px] text-muted-foreground">
                    {formatDayShort(appointment.starts_at)} · {formatTime(appointment.starts_at)} ·{' '}
                    {APPOINTMENT_STATUS_LABELS[appointment.status]}
                  </div>
                </div>
                <div className="shrink-0 text-[14px] font-semibold text-primary">
                  {formatPrice(appointment.price)}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <Button
        variant="ghost"
        className="w-full text-muted-foreground hover:text-destructive"
        onClick={() => setConfirmDelete(true)}
      >
        <Trash2 />
        Удалить клиента
      </Button>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить клиента?</DialogTitle>
            <DialogDescription>
              Карточка, история записей и фото «{client.name}» будут удалены безвозвратно.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <DialogClose asChild>
              <Button variant="secondary">Отмена</Button>
            </DialogClose>
            <Button
              variant="destructive"
              disabled={remove.isPending}
              onClick={() =>
                remove.mutate(client.id, {
                  onSuccess: () => navigate('/clients', { replace: true }),
                })
              }
            >
              Удалить
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
