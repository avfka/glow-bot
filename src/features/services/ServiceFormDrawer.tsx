import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import type { Service } from '@/types/domain';

import { useCreateService, useUpdateService } from './api';

interface ServiceFormDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** null — создание новой услуги */
  service: Service | null;
}

export function ServiceFormDrawer({ open, onOpenChange, service }: ServiceFormDrawerProps) {
  const create = useCreateService();
  const update = useUpdateService();
  const isPending = create.isPending || update.isPending;

  const [name, setName] = useState('');
  const [durationMin, setDurationMin] = useState('60');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    if (!open) return;
    setName(service?.name ?? '');
    setDurationMin(String(service?.duration_min ?? 60));
    setPrice(service ? String(service.price) : '');
    setDescription(service?.description ?? '');
  }, [open, service]);

  const canSubmit = name.trim().length > 0 && Number(durationMin) > 0 && Number(price) >= 0;

  const submit = () => {
    if (!canSubmit || isPending) return;
    const payload = {
      name: name.trim(),
      duration_min: Number(durationMin),
      price: Number(price) || 0,
      description: description.trim(),
    };
    const onSuccess = () => onOpenChange(false);
    if (service) {
      update.mutate({ id: service.id, ...payload }, { onSuccess });
    } else {
      create.mutate(payload, { onSuccess });
    }
  };

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>{service ? 'Редактировать услугу' : 'Новая услуга'}</DrawerTitle>
          <DrawerDescription>
            {service ? 'Изменения не затронут уже созданные записи' : 'Добавьте услугу в каталог'}
          </DrawerDescription>
        </DrawerHeader>

        <div className="space-y-4 overflow-y-auto px-5 py-5">
          <div className="space-y-2">
            <Label htmlFor="service-name">Название</Label>
            <Input
              id="service-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Чистка лица"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="service-duration">Длительность, мин</Label>
              <Input
                id="service-duration"
                type="number"
                inputMode="numeric"
                min={5}
                step={5}
                value={durationMin}
                onChange={(e) => setDurationMin(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="service-price">Цена, ₽</Label>
              <Input
                id="service-price"
                type="number"
                inputMode="numeric"
                min={0}
                step={100}
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="3500"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="service-description">Описание</Label>
            <Textarea
              id="service-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Что входит в процедуру, подготовка, противопоказания…"
            />
          </div>
        </div>

        <div
          className="px-5 pt-1"
          style={{ paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 1.25rem)' }}
        >
          <Button className="w-full" size="lg" disabled={!canSubmit || isPending} onClick={submit}>
            {isPending ? 'Сохраняем…' : service ? 'Сохранить' : 'Добавить услугу'}
          </Button>
        </div>
      </DrawerContent>
    </Drawer>
  );
}
