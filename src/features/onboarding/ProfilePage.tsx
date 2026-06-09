import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/shared/PageHeader';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useMainButton } from '@/hooks/useMainButton';
import { useSession } from '@/stores/session';

import { useUpdateSpecialist } from './api';

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('');
}

export function ProfilePage() {
  const specialist = useSession((s) => s.specialist);
  const navigate = useNavigate();
  const update = useUpdateSpecialist();

  const [name, setName] = useState(specialist?.name ?? '');
  const [specialization, setSpecialization] = useState(specialist?.specialization ?? '');
  const [phone, setPhone] = useState(specialist?.phone ?? '');

  const canSubmit = name.trim().length > 1 && specialization.trim().length > 1;

  const submit = () => {
    if (!canSubmit || update.isPending) return;
    update.mutate(
      { name: name.trim(), specialization: specialization.trim(), phone: phone.trim() },
      { onSuccess: () => navigate(-1) },
    );
  };

  useMainButton({
    text: 'Сохранить',
    onClick: submit,
    enabled: canSubmit,
    loading: update.isPending,
  });

  if (!specialist) return null;

  return (
    <div>
      <PageHeader title="Профиль" subtitle="Данные видны только вам" />

      <div className="mb-7 flex items-center gap-4">
        <Avatar className="size-16">
          {specialist.avatar_url ? <AvatarImage src={specialist.avatar_url} alt="" /> : null}
          <AvatarFallback className="text-lg">{initials(specialist.name || '·')}</AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <div className="truncate font-semibold">{specialist.name}</div>
          <div className="truncate text-sm text-muted-foreground">{specialist.specialization}</div>
        </div>
      </div>

      <div className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="name">Имя</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="specialization">Специализация</Label>
          <Input
            id="specialization"
            value={specialization}
            onChange={(e) => setSpecialization(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="phone">Телефон</Label>
          <Input id="phone" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
      </div>

      {update.isError ? (
        <p className="mt-4 text-sm text-destructive">
          {update.error instanceof Error ? update.error.message : 'Не удалось сохранить'}
        </p>
      ) : null}
    </div>
  );
}
