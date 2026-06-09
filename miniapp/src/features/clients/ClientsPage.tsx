import { motion } from 'framer-motion';
import { Plus, Search, Users } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/shared/EmptyState';
import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { PageHeader } from '@/components/shared/PageHeader';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { plural } from '@/lib/format';
import { haptics } from '@/lib/telegram';
import { SKIN_TYPE_LABELS } from '@/types/domain';

import { useClients } from './api';

function clientInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('');
}

export function ClientsPage() {
  const [search, setSearch] = useState('');
  const { data: clients, isPending, isError } = useClients(search);
  const navigate = useNavigate();

  return (
    <div>
      <PageHeader
        title="Клиенты"
        subtitle={clients ? plural(clients.length, 'клиент', 'клиента', 'клиентов') : undefined}
        action={
          <Button
            size="icon"
            aria-label="Добавить клиента"
            onClick={() => {
              haptics.impact();
              navigate('/clients/new');
            }}
          >
            <Plus />
          </Button>
        }
      />

      <div className="relative mb-5">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-[18px] -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Имя или телефон"
          className="pl-11"
          type="search"
        />
      </div>

      {isPending ? (
        <ListSkeleton count={6} itemHeight={72} />
      ) : isError ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Не удалось загрузить клиентов.
        </p>
      ) : clients.length === 0 ? (
        search ? (
          <EmptyState
            icon={Search}
            title="Никого не нашли"
            description="Попробуйте изменить запрос или добавьте нового клиента."
          />
        ) : (
          <EmptyState
            icon={Users}
            title="Пока нет клиентов"
            description="Заведите карточку первого клиента — контакты, тип кожи и историю процедур."
            action={
              <Button asChild>
                <Link to="/clients/new">
                  <Plus />
                  Добавить клиента
                </Link>
              </Button>
            }
          />
        )
      ) : (
        <div className="space-y-2.5">
          {clients.map((client, i) => (
            <motion.div
              key={client.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: Math.min(i * 0.03, 0.25), ease: 'easeOut' }}
            >
              <Link
                to={`/clients/${client.id}`}
                onClick={() => haptics.selection()}
                className="flex items-center gap-3.5 rounded-2xl bg-card p-4 shadow-soft transition-transform active:scale-[0.99]"
              >
                <Avatar>
                  <AvatarFallback>{clientInitials(client.name)}</AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[15px] font-medium">{client.name}</div>
                  {client.phone ? (
                    <div className="truncate text-[13px] text-muted-foreground">{client.phone}</div>
                  ) : null}
                </div>
                {client.skin_type ? (
                  <Badge variant="secondary" className="shrink-0">
                    {SKIN_TYPE_LABELS[client.skin_type]}
                  </Badge>
                ) : null}
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
