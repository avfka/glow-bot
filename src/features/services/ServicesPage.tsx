import { motion } from 'framer-motion';
import { Clock, Plus, Tag, Trash2 } from 'lucide-react';
import { useState } from 'react';

import { EmptyState } from '@/components/shared/EmptyState';
import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { PageHeader } from '@/components/shared/PageHeader';
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
import { Switch } from '@/components/ui/switch';
import { formatDuration, formatPrice } from '@/lib/format';
import { haptics } from '@/lib/telegram';
import type { Service } from '@/types/domain';

import { useDeleteService, useServices, useUpdateService } from './api';
import { ServiceFormDrawer } from './ServiceFormDrawer';

export function ServicesPage() {
  const { data: services, isPending, isError } = useServices();
  const update = useUpdateService();
  const remove = useDeleteService();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Service | null>(null);
  const [deleting, setDeleting] = useState<Service | null>(null);

  const openCreate = () => {
    haptics.impact();
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (service: Service) => {
    haptics.impact();
    setEditing(service);
    setFormOpen(true);
  };

  return (
    <div>
      <PageHeader
        title="Услуги"
        subtitle="Каталог процедур и прайс"
        action={
          <Button size="icon" aria-label="Добавить услугу" onClick={openCreate}>
            <Plus />
          </Button>
        }
      />

      {isPending ? (
        <ListSkeleton count={4} itemHeight={96} />
      ) : isError ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Не удалось загрузить услуги. Потяните вниз, чтобы обновить.
        </p>
      ) : services.length === 0 ? (
        <EmptyState
          icon={Tag}
          title="Пока нет услуг"
          description="Добавьте первую процедуру — она появится при создании записи."
          action={
            <Button onClick={openCreate}>
              <Plus />
              Добавить услугу
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {services.map((service, i) => (
            <motion.div
              key={service.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: Math.min(i * 0.04, 0.3), ease: 'easeOut' }}
            >
              <Card className={service.is_active ? '' : 'opacity-55'}>
                <CardContent className="p-5">
                  <button
                    type="button"
                    className="block w-full text-left"
                    onClick={() => openEdit(service)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-[15px] font-semibold">{service.name}</div>
                        <div className="mt-1 flex items-center gap-1.5 text-[13px] text-muted-foreground">
                          <Clock className="size-3.5" />
                          {formatDuration(service.duration_min)}
                        </div>
                      </div>
                      <div className="shrink-0 text-[15px] font-semibold text-primary">
                        {formatPrice(service.price)}
                      </div>
                    </div>
                    {service.description ? (
                      <p className="mt-2.5 line-clamp-2 text-[13px] leading-relaxed text-muted-foreground">
                        {service.description}
                      </p>
                    ) : null}
                  </button>

                  <div className="mt-4 flex items-center justify-between border-t border-border/70 pt-3.5">
                    <label className="flex items-center gap-2.5 text-[13px] text-muted-foreground">
                      <Switch
                        checked={service.is_active}
                        onCheckedChange={(checked) => {
                          haptics.selection();
                          update.mutate({ id: service.id, is_active: checked });
                        }}
                      />
                      {service.is_active ? 'Активна' : 'Скрыта'}
                    </label>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Удалить услугу"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => setDeleting(service)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <ServiceFormDrawer open={formOpen} onOpenChange={setFormOpen} service={editing} />

      <Dialog open={deleting !== null} onOpenChange={(open) => !open && setDeleting(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить услугу?</DialogTitle>
            <DialogDescription>
              «{deleting?.name}» будет удалена из каталога. История записей сохранится.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <DialogClose asChild>
              <Button variant="secondary">Отмена</Button>
            </DialogClose>
            <Button
              variant="destructive"
              disabled={remove.isPending}
              onClick={() => {
                if (!deleting) return;
                remove.mutate(deleting.id, { onSuccess: () => setDeleting(null) });
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
