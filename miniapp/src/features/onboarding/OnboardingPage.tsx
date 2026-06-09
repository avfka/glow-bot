import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useMainButton } from '@/hooks/useMainButton';
import { useSession } from '@/stores/session';

import { useUpdateSpecialist } from './api';

const SUGGESTED_SPECIALIZATIONS = [
  'Косметолог-эстетист',
  'Дерматокосметолог',
  'Массажист',
  'Бровист',
  'Лэшмейкер',
];

export function OnboardingPage() {
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
      {
        name: name.trim(),
        specialization: specialization.trim(),
        phone: phone.trim(),
        onboarded_at: new Date().toISOString(),
      },
      { onSuccess: () => navigate('/', { replace: true }) },
    );
  };

  useMainButton({
    text: 'Начать работу',
    onClick: submit,
    enabled: canSubmit,
    loading: update.isPending,
  });

  if (specialist?.onboarded_at) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col px-6 pb-10 pt-14">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className="mb-7 flex size-14 items-center justify-center rounded-2xl bg-accent">
          <Sparkles className="size-6 text-accent-foreground" strokeWidth={1.6} />
        </div>
        <h1 className="text-[28px] font-semibold leading-tight tracking-tight">
          Добро пожаловать
          <br />в Glow Studio
        </h1>
        <p className="mt-2.5 text-[15px] leading-relaxed text-muted-foreground">
          Ваше рабочее место: клиенты, записи, услуги и AI-разбор составов — в одном приложении.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.12, ease: 'easeOut' }}
        className="mt-9 space-y-5"
      >
        <div className="space-y-2">
          <Label htmlFor="name">Ваше имя</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Анна Иванова"
            autoComplete="name"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="specialization">Специализация</Label>
          <Input
            id="specialization"
            value={specialization}
            onChange={(e) => setSpecialization(e.target.value)}
            placeholder="Косметолог-эстетист"
          />
          <div className="flex flex-wrap gap-1.5 pt-1">
            {SUGGESTED_SPECIALIZATIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSpecialization(s)}
                className="rounded-full bg-secondary px-3 py-1.5 text-[13px] text-secondary-foreground transition-colors active:bg-accent"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone">Телефон для клиентов</Label>
          <Input
            id="phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+7 900 000-00-00"
            autoComplete="tel"
          />
          <p className="text-xs text-muted-foreground">Необязательно — можно добавить позже.</p>
        </div>
      </motion.div>

      {update.isError ? (
        <p className="mt-4 text-sm text-destructive">
          {update.error instanceof Error ? update.error.message : 'Не удалось сохранить'}
        </p>
      ) : null}
    </div>
  );
}
