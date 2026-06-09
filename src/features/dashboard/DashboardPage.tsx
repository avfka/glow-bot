import { addDays, startOfDay } from 'date-fns';
import { motion } from 'framer-motion';
import { CalendarDays, ChevronRight, Plus } from 'lucide-react';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAppointmentsRange } from '@/features/appointments/api';
import { AppointmentCard } from '@/features/appointments/AppointmentCard';
import { formatDay, formatPrice, formatTime, plural } from '@/lib/format';
import { cn } from '@/lib/cn';
import { useSession } from '@/stores/session';

import { useDashboardStats } from './api';
import { FaceHero } from './FaceHero';

function greeting(): string {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 11) return 'Доброе утро';
  if (hour >= 11 && hour < 17) return 'Добрый день';
  if (hour >= 17 && hour < 23) return 'Добрый вечер';
  return 'Доброй ночи';
}

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('');
}

function StatCard({
  label,
  value,
  tone,
  delay,
}: {
  label: string;
  value: string;
  tone: 'lavender' | 'peach' | 'sage';
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: 'easeOut' }}
      className={cn('rounded-2xl p-4', {
        'bg-pastel-lavender': tone === 'lavender',
        'bg-pastel-peach': tone === 'peach',
        'bg-pastel-sage': tone === 'sage',
      })}
    >
      <div className="text-[19px] font-semibold leading-tight tracking-tight">{value}</div>
      <div className="mt-1 text-[12px] leading-snug text-foreground/60">{label}</div>
    </motion.div>
  );
}

export function DashboardPage() {
  const specialist = useSession((s) => s.specialist);
  const { data: stats, isPending: statsLoading } = useDashboardStats();

  const { todayFrom, todayTo, upcomingTo } = useMemo(() => {
    const from = startOfDay(new Date());
    return {
      todayFrom: from.toISOString(),
      todayTo: addDays(from, 1).toISOString(),
      upcomingTo: addDays(from, 15).toISOString(),
    };
  }, []);

  const { data: today, isPending: todayLoading } = useAppointmentsRange(todayFrom, todayTo);
  const { data: upcoming } = useAppointmentsRange(todayTo, upcomingTo);
  const nextUpcoming = (upcoming ?? []).filter((a) => a.status === 'scheduled').slice(0, 4);

  const firstName = specialist?.name.split(' ')[0] ?? '';

  return (
    <div>
      <header className="mb-2 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{greeting()},</p>
          <h1 className="text-[24px] font-semibold leading-tight tracking-tight">{firstName}</h1>
        </div>
        <Link to="/profile" aria-label="Профиль">
          <Avatar className="size-12 ring-2 ring-card">
            {specialist?.avatar_url ? <AvatarImage src={specialist.avatar_url} alt="" /> : null}
            <AvatarFallback>{initials(specialist?.name ?? '·')}</AvatarFallback>
          </Avatar>
        </Link>
      </header>

      <FaceHero />

      <section className="mt-2 grid grid-cols-3 gap-2.5">
        {statsLoading || !stats ? (
          <>
            <Skeleton className="h-[76px]" />
            <Skeleton className="h-[76px]" />
            <Skeleton className="h-[76px]" />
          </>
        ) : (
          <>
            <StatCard
              tone="lavender"
              value={String(stats.clientsCount)}
              label={plural(stats.clientsCount, 'клиент', 'клиента', 'клиентов').replace(/^\d+ /, '')}
              delay={0.05}
            />
            <StatCard
              tone="peach"
              value={String(stats.weekAppointments)}
              label="записей на неделе"
              delay={0.12}
            />
            <StatCard
              tone="sage"
              value={formatPrice(stats.monthRevenue)}
              label="выручка за месяц"
              delay={0.19}
            />
          </>
        )}
      </section>

      <section className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold">Сегодня</h2>
          <Button variant="ghost" size="sm" asChild className="-mr-2 text-muted-foreground">
            <Link to="/appointments">
              Календарь
              <ChevronRight className="size-4" />
            </Link>
          </Button>
        </div>

        {todayLoading ? (
          <ListSkeleton count={2} itemHeight={80} />
        ) : !today || today.length === 0 ? (
          <div className="flex flex-col items-center rounded-2xl bg-card px-6 py-8 text-center shadow-soft">
            <CalendarDays className="mb-3 size-6 text-muted-foreground" strokeWidth={1.6} />
            <p className="text-sm text-muted-foreground">Сегодня записей нет — день свободен.</p>
            <Button size="sm" className="mt-4" asChild>
              <Link to="/appointments/new">
                <Plus />
                Новая запись
              </Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-2.5">
            {today.map((appointment) => (
              <AppointmentCard key={appointment.id} appointment={appointment} />
            ))}
          </div>
        )}
      </section>

      {nextUpcoming.length > 0 ? (
        <section className="mt-8">
          <h2 className="mb-3 text-[15px] font-semibold">Ближайшие</h2>
          <div className="space-y-2.5">
            {nextUpcoming.map((appointment) => (
              <Link
                key={appointment.id}
                to={`/appointments/${appointment.id}/edit`}
                className="flex items-center gap-3.5 rounded-2xl bg-card p-4 shadow-soft"
              >
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[14px] font-medium">
                    {appointment.client?.name ?? 'Клиент'}
                  </div>
                  <div className="truncate text-[13px] text-muted-foreground">
                    {appointment.service?.name ?? 'Без услуги'}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-[14px] font-medium">{formatDay(appointment.starts_at)}</div>
                  <div className="text-[13px] text-muted-foreground">
                    {formatTime(appointment.starts_at)}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
