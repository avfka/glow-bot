import {
  addDays,
  addWeeks,
  eachDayOfInterval,
  endOfWeek,
  format,
  isSameDay,
  isToday,
  startOfDay,
  startOfWeek,
} from 'date-fns';
import { ru } from 'date-fns/locale';
import { motion } from 'framer-motion';
import { CalendarDays, ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/shared/EmptyState';
import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/cn';
import { formatDay } from '@/lib/format';
import { haptics } from '@/lib/telegram';
import type { AppointmentWithRelations } from '@/types/domain';

import { useAppointmentsRange } from './api';
import { AppointmentCard } from './AppointmentCard';

type ViewMode = 'day' | 'week';

const WEEK_OPTS = { weekStartsOn: 1 as const };

/** Горизонтальная лента дат на две недели вперёд (и 3 дня назад). */
function DateStrip({ selected, onSelect }: { selected: Date; onSelect: (d: Date) => void }) {
  const days = useMemo(() => {
    const start = addDays(startOfDay(new Date()), -3);
    return Array.from({ length: 17 }, (_, i) => addDays(start, i));
  }, []);

  return (
    <div className="scrollbar-none -mx-5 mb-5 flex gap-2 overflow-x-auto px-5 pb-1">
      {days.map((day) => {
        const active = isSameDay(day, selected);
        return (
          <button
            key={day.toISOString()}
            type="button"
            onClick={() => {
              haptics.selection();
              onSelect(day);
            }}
            className={cn(
              'flex w-[52px] shrink-0 flex-col items-center rounded-2xl py-2.5 transition-colors',
              active ? 'bg-primary text-primary-foreground shadow-soft' : 'bg-card shadow-soft',
            )}
          >
            <span
              className={cn(
                'text-[11px] uppercase',
                active ? 'text-primary-foreground/80' : 'text-muted-foreground',
              )}
            >
              {format(day, 'EEEEEE', { locale: ru })}
            </span>
            <span className="mt-0.5 text-[17px] font-semibold leading-tight">
              {format(day, 'd')}
            </span>
            {isToday(day) && !active ? (
              <span className="mt-0.5 size-1 rounded-full bg-primary" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

function DayView({ selected, onSelect }: { selected: Date; onSelect: (d: Date) => void }) {
  const from = startOfDay(selected);
  const to = addDays(from, 1);
  const { data, isPending } = useAppointmentsRange(from.toISOString(), to.toISOString());

  return (
    <div>
      <DateStrip selected={selected} onSelect={onSelect} />
      {isPending ? (
        <ListSkeleton count={4} itemHeight={80} />
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title={`${formatDay(selected)} записей нет`}
          description="День свободен. Добавьте запись, чтобы спланировать его."
          action={
            <Button asChild>
              <Link to={`/appointments/new?date=${format(selected, 'yyyy-MM-dd')}`}>
                <Plus />
                Новая запись
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-2.5">
          {data.map((appointment) => (
            <AppointmentCard key={appointment.id} appointment={appointment} />
          ))}
        </div>
      )}
    </div>
  );
}

function WeekView() {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date(), WEEK_OPTS));
  const weekEnd = endOfWeek(weekStart, WEEK_OPTS);
  const { data, isPending } = useAppointmentsRange(
    weekStart.toISOString(),
    addDays(weekEnd, 1).toISOString(),
  );

  const byDay = useMemo(() => {
    const days = eachDayOfInterval({ start: weekStart, end: weekEnd });
    return days.map((day) => ({
      day,
      items: (data ?? []).filter((a) => isSameDay(new Date(a.starts_at), day)),
    }));
  }, [data, weekStart, weekEnd]);

  const shiftWeek = (delta: number) => {
    haptics.selection();
    setWeekStart((prev) => addWeeks(prev, delta));
  };

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <Button variant="secondary" size="icon-sm" aria-label="Прошлая неделя" onClick={() => shiftWeek(-1)}>
          <ChevronLeft className="size-4" />
        </Button>
        <span className="text-[14px] font-medium">
          {format(weekStart, 'd MMM', { locale: ru })} — {format(weekEnd, 'd MMM', { locale: ru })}
        </span>
        <Button variant="secondary" size="icon-sm" aria-label="Следующая неделя" onClick={() => shiftWeek(1)}>
          <ChevronRight className="size-4" />
        </Button>
      </div>

      {isPending ? (
        <ListSkeleton count={5} itemHeight={72} />
      ) : (
        <div className="space-y-6">
          {byDay.every(({ items }) => items.length === 0) ? (
            <EmptyState
              icon={CalendarDays}
              title="Неделя свободна"
              description="На эту неделю записей пока нет."
            />
          ) : (
            byDay
              .filter(({ items }) => items.length > 0)
              .map(({ day, items }) => (
                <section key={day.toISOString()}>
                  <h3
                    className={cn(
                      'mb-2.5 text-[13px] font-semibold uppercase tracking-wide',
                      isToday(day) ? 'text-primary' : 'text-muted-foreground',
                    )}
                  >
                    {format(day, 'EEEE, d MMMM', { locale: ru })}
                  </h3>
                  <div className="space-y-2.5">
                    {items.map((appointment: AppointmentWithRelations) => (
                      <AppointmentCard key={appointment.id} appointment={appointment} />
                    ))}
                  </div>
                </section>
              ))
          )}
        </div>
      )}
    </div>
  );
}

export function AppointmentsPage() {
  const [mode, setMode] = useState<ViewMode>('day');
  const [selectedDay, setSelectedDay] = useState(() => startOfDay(new Date()));
  const navigate = useNavigate();

  return (
    <div>
      <PageHeader
        title="Записи"
        action={
          <Button
            size="icon"
            aria-label="Новая запись"
            onClick={() => {
              haptics.impact();
              navigate(`/appointments/new?date=${format(selectedDay, 'yyyy-MM-dd')}`);
            }}
          >
            <Plus />
          </Button>
        }
      />

      <Tabs value={mode} onValueChange={(v) => setMode(v as ViewMode)} className="mb-5">
        <TabsList>
          <TabsTrigger value="day">День</TabsTrigger>
          <TabsTrigger value="week">Неделя</TabsTrigger>
        </TabsList>
      </Tabs>

      <motion.div
        key={mode}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        {mode === 'day' ? (
          <DayView selected={selectedDay} onSelect={setSelectedDay} />
        ) : (
          <WeekView />
        )}
      </motion.div>
    </div>
  );
}
