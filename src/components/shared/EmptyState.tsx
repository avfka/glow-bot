import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={cn('flex flex-col items-center px-8 py-16 text-center', className)}
    >
      <div className="mb-5 flex size-16 items-center justify-center rounded-full bg-accent">
        <Icon className="size-7 text-accent-foreground" strokeWidth={1.6} />
      </div>
      <h3 className="text-[15px] font-semibold">{title}</h3>
      {description ? (
        <p className="mt-1.5 max-w-[260px] text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </motion.div>
  );
}
