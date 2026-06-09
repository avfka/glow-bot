import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ListSkeleton } from '@/components/shared/ListSkeleton';
import { PageHeader } from '@/components/shared/PageHeader';
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
import { useMainButton } from '@/hooks/useMainButton';
import type { SkinType } from '@/types/database';
import { SKIN_TYPE_LABELS } from '@/types/domain';

import { useClient, useCreateClient, useUpdateClient } from './api';

const SKIN_TYPES = Object.keys(SKIN_TYPE_LABELS) as SkinType[];
const SKIN_TYPE_NONE = 'none';

export function ClientFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const { data: client, isPending: clientLoading } = useClient(id);
  const create = useCreateClient();
  const update = useUpdateClient();
  const isPending = create.isPending || update.isPending;

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [telegramUsername, setTelegramUsername] = useState('');
  const [skinType, setSkinType] = useState<string>(SKIN_TYPE_NONE);
  const [allergies, setAllergies] = useState('');
  const [contraindications, setContraindications] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!client) return;
    setName(client.name);
    setPhone(client.phone);
    setTelegramUsername(client.telegram_username);
    setSkinType(client.skin_type ?? SKIN_TYPE_NONE);
    setAllergies(client.allergies);
    setContraindications(client.contraindications);
    setNotes(client.notes);
  }, [client]);

  const canSubmit = name.trim().length > 1;

  const submit = () => {
    if (!canSubmit || isPending) return;
    const payload = {
      name: name.trim(),
      phone: phone.trim(),
      telegram_username: telegramUsername.trim().replace(/^@/, ''),
      skin_type: skinType === SKIN_TYPE_NONE ? null : (skinType as SkinType),
      allergies: allergies.trim(),
      contraindications: contraindications.trim(),
      notes: notes.trim(),
    };
    if (isEdit && id) {
      update.mutate({ id, ...payload }, { onSuccess: () => navigate(-1) });
    } else {
      create.mutate(payload, {
        onSuccess: (created) => navigate(`/clients/${created.id}`, { replace: true }),
      });
    }
  };

  useMainButton({
    text: isEdit ? 'Сохранить' : 'Добавить клиента',
    onClick: submit,
    enabled: canSubmit,
    loading: isPending,
  });

  if (isEdit && clientLoading) {
    return (
      <div>
        <PageHeader title="Клиент" />
        <ListSkeleton count={5} itemHeight={64} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={isEdit ? 'Редактировать' : 'Новый клиент'}
        subtitle={isEdit ? client?.name : 'Карточка клиента'}
      />

      <div className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="client-name">Имя</Label>
          <Input
            id="client-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Мария Петрова"
            autoComplete="off"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="client-phone">Телефон</Label>
            <Input
              id="client-phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+7 900…"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="client-tg">Telegram</Label>
            <Input
              id="client-tg"
              value={telegramUsername}
              onChange={(e) => setTelegramUsername(e.target.value)}
              placeholder="@username"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Тип кожи</Label>
          <Select value={skinType} onValueChange={setSkinType}>
            <SelectTrigger>
              <SelectValue placeholder="Не указан" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={SKIN_TYPE_NONE}>Не указан</SelectItem>
              {SKIN_TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {SKIN_TYPE_LABELS[t]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-allergies">Аллергии</Label>
          <Textarea
            id="client-allergies"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            placeholder="Например: ретинол, эфирные масла цитрусовых"
            className="min-h-[72px]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-contra">Противопоказания</Label>
          <Textarea
            id="client-contra"
            value={contraindications}
            onChange={(e) => setContraindications(e.target.value)}
            placeholder="Например: купероз, беременность"
            className="min-h-[72px]"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-notes">Заметки</Label>
          <Textarea
            id="client-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Пожелания, особенности, история"
          />
        </div>
      </div>

      {(create.isError || update.isError) && (
        <p className="mt-4 text-sm text-destructive">Не удалось сохранить. Попробуйте ещё раз.</p>
      )}
    </div>
  );
}
