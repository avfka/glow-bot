import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';
import { useEffect, type ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import { useSession } from '@/stores/session';

function Splash() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="text-center"
      >
        <motion.div
          animate={{ opacity: [1, 0.55, 1] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
          className="text-2xl font-semibold tracking-tight"
        >
          Glow Studio
        </motion.div>
        <p className="mt-2 text-sm text-muted-foreground">Подготавливаем рабочее место…</p>
      </motion.div>
    </div>
  );
}

function AuthError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-8 text-center">
      <h1 className="text-lg font-semibold">Не удалось войти</h1>
      <p className="mt-2 max-w-[280px] text-sm leading-relaxed text-muted-foreground">{message}</p>
      <Button className="mt-6" variant="secondary" onClick={onRetry}>
        <RefreshCw />
        Попробовать снова
      </Button>
    </div>
  );
}

export function AuthGate({ children }: { children: ReactNode }) {
  const { status, error, authenticate } = useSession();

  useEffect(() => {
    void authenticate();
  }, [authenticate]);

  if (status === 'loading') return <Splash />;
  if (status === 'error') {
    return <AuthError message={error ?? 'Неизвестная ошибка'} onRetry={() => void authenticate()} />;
  }
  return <>{children}</>;
}
