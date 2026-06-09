import { CalendarDays, FlaskConical, Home, Tag, Users } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { cn } from '@/lib/cn';
import { haptics } from '@/lib/telegram';

interface TabItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const TABS: TabItem[] = [
  { to: '/', label: 'Главная', icon: Home },
  { to: '/appointments', label: 'Записи', icon: CalendarDays },
  { to: '/clients', label: 'Клиенты', icon: Users },
  { to: '/services', label: 'Услуги', icon: Tag },
  { to: '/analyzer', label: 'Состав', icon: FlaskConical },
];

export function TabBar() {
  return (
    <nav
      className="fixed inset-x-0 z-40 flex justify-center"
      style={{ bottom: 'calc(env(safe-area-inset-bottom, 0px) + 1rem)' }}
    >
      <div className="flex items-center gap-1 rounded-full bg-foreground/95 p-1.5 shadow-float backdrop-blur dark:bg-card/95 dark:ring-1 dark:ring-border">
        {TABS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            aria-label={label}
            onClick={() => haptics.selection()}
            className={({ isActive }) =>
              cn(
                'flex size-12 items-center justify-center rounded-full transition-colors duration-200',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-background/70 hover:text-background dark:text-muted-foreground dark:hover:text-foreground',
              )
            }
          >
            <Icon className="size-[21px]" strokeWidth={1.8} />
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
