import { format } from 'date-fns';
import { Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useClients } from '@/features/clients/api';
import { useServices } from '@/features/services/api';
import { useMainButton } from '@/hooks/useMainButton';
import type { AppointmentStatus } from '@/types/database';
import { APPOINTMENT_STATUS_LABELS } from '@/types/domain';

import {
  useAppointment,
  useCreateAppointment,
  useDeleteAppointment,
  useUpdateAppointment,
} from './api';

const REMINDER_NONE = 'none';
const REMINDER_OPTIONS = [
  { value: '60', label: 'За 1 час' },
  { value: '180', label: 'За 3 часа' },
  { value: '1440', label: 'За сутки' },
];

const STATUSES = Object.keys(APPOINTMENT_STATUS_LABELS) as AppointmentStatus[];

export function AppointmentFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const { data: appointment, isPending: appointmentLoading } = useAppointment(id);
  const { data: clients } = useClients('');
  const { data: services } = useServices();
  const activeServices = (services ?? []).filter((s) => s.is_active);

  const create = useCreateAppointment();
  const update = useUpdateAppointment();
  const remove = useDeleteAppointment();
  const isPending = create.isPending || update.isPending;

  const [clientId, setClientId] = useState('');
  const [serviceId, setServiceId] = useState('');
  const [date, setDate] = useState(searchParams.get('date') ?? format(new Date(), 'yyyy-MM-dd'));
  const [time, setTime] = useState('10:00');
  const [durationMin, setDurationMin] = useState('60');
  const [price, setPrice] = useState('0');
  const [status, setStatus] = useState<AppointmentStatus>('scheduled');
  const [note, setNote] = useState('');
  const [reminder, setReminder] = useState(REMINDER_NONE);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!appointment) return;
    const startsAt = new Date(appointment.starts_at);
    setClientId(appointment.client_id);
    setServiceId(appointment.service_id ?? '');
    setDate(format(startsAt, 'yyyy-MM-dd'));
    setTime(format(startsAt, 'HH:mm'));
    setDurationMin(String(appointment.duration_min));
    setPrice(String(appointment.price));
    setStatus(appointment.status);
    setNote(appointment.note);
    setReminder(appointment.remind_before_min ? String(appointment.remind_before_min) : REMINDER_NONE);
  }, [appointment]);

  /** При выборе услуги подставляем её длительность и цену. */
  const onServiceChange = (nextServiceId: string) => {
    setServiceId(nextServiceId);
    const service = activeServices.find((s) => s.id === nextServiceId);
    if (service) {
      setDurationMin(String(service.duration_min));
      setPrice(String(service.price));
    }
  };

  const canSubmit = Boolean(clientId) && Boolean(date) && Boolean(time) && Number(durationMin) > 0;

  const submit = () => {
    if (!canSubmit || isPending) return;
    const payload = {
      client_id: clientId,
      service_id: serviceId || null,
      starts_at: new Date(`${date}T${time}`).toISOString(),
      duration_min: Number(durationMin),
      price: Number(price) || 0,
      status,
      note: note.trim(),
      remind_before_min: reminder === REMINDER_NONE ? null : Number(reminder),
    };
    if (isEdit && id) {
      update.mutate({ id, ...payload }, { onSuccess: () => navigate(-1) });
    } else {
      create.mutate(payload, { onSuccess: () => navigate(-1) });
    }
  };

  useMainButton({
    text: isEdit ? 'Сохранить' : 'Создать запись',
    onClick: submit,
    enabled: canSubmit,
    loading: isPending,
  });

  if (isEdit && appointmentLoading) {
    return (
      <div>
        <PageHeader title="Запись" />
        <ListSkeleton count={5} itemHeight={64} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={isEdit ? 'Редактировать запись' : 'Новая запись'} />

      <div className="space-y-5">
        <div className="space-y-2">
          <Label>Клиент</Label>
          <Select value={clientId} onValueChange={setClientId}>
            <SelectTrigger>
              <SelectValue placeholder="Выберите клиента" />
            </SelectTrigger>
            <SelectContent>
              {(clients ?? []).map((client) => (
                <SelectItem key={client.id} value={client.id}>
                  {client.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {clients && clients.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Сначала добавьте клиента на вкладке «Клиенты».
            </p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label>Услуга</Label>
          <Select value={serviceId} onValueChange={onServiceChange}>
            <SelectTrigger>
              <SelectValue placeholder="Выберите услугу" />
            </SelectTrigger>
            <SelectContent>
              {activeServices.map((service) => (
                <SelectItem key={service.id} value={service.id}>
                  {service.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="appt-date">Дата</Label>
            <Input id="appt-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="appt-time">Время</Label>
            <Input id="appt-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="appt-duration">Длительность, мин</Label>
            <Input
              id="appt-duration"
              type="number"
              inputMode="numeric"
              min={5}
              step={5}
              value={durationMin}
              onChange={(e) => setDurationMin(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="appt-price">Цена, ₽</Label>
            <Input
              id="appt-price"
              type="number"
              inputMode="numeric"
              min={0}
              step={100}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
        </div>

        {isEdit ? (
          <div className="space-y-2">
            <Label>Статус</Label>
            <Select value={status} onValueChange={(v) => setStatus(v as AppointmentStatus)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {APPOINTMENT_STATUS_LABELS[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}

        <div className="space-y-2">
          <Label>Напоминание в Telegram</Label>
          <Select value={reminder} onValueChange={setReminder}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={REMINDER_NONE}>Без напоминания</SelectItem>
              {REMINDER_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="appt-note">Заметка</Label>
          <Textarea
            id="appt-note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Пожелания клиента, подготовка к процедуре…"
          />
        </div>

        {isEdit ? (
          <Button
            variant="ghost"
            className="w-full text-muted-foreground hover:text-destructive"
            onClick={() => setConfirmDelete(true)}
          >
            <Trash2 />
            Удалить запись
          </Button>
        ) : null}
      </div>

      {(create.isError || update.isError) && (
        <p className="mt-4 text-sm text-destructive">Не удалось сохранить. Попробуйте ещё раз.</p>
      )}

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить запись?</DialogTitle>
            <DialogDescription>Запись будет удалена из календаря безвозвратно.</DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <DialogClose asChild>
              <Button variant="secondary">Отмена</Button>
            </DialogClose>
            <Button
              variant="destructive"
              disabled={remove.isPending}
              onClick={() => {
                if (!id) return;
                remove.mutate(id, { onSuccess: () => navigate('/appointments', { replace: true }) });
              }}
            >
              Удалить
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
