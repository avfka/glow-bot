import { AnimatePresence, motion } from 'framer-motion';
import { Outlet, useLocation } from 'react-router-dom';

import { useBackButton } from '@/hooks/useBackButton';

import { TabBar } from './TabBar';

const TAB_ROUTES = new Set(['/', '/appointments', '/clients', '/services', '/analyzer']);

export function AppShell() {
  const location = useLocation();
  const isTabRoute = TAB_ROUTES.has(location.pathname);

  useBackButton(!isTabRoute);

  return (
    <div className="mx-auto min-h-dvh w-full max-w-md">
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.main
          key={location.pathname}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          className="px-5 pt-5 pb-safe-tabbar"
        >
          <Outlet />
        </motion.main>
      </AnimatePresence>
      {isTabRoute ? <TabBar /> : null}
    </div>
  );
}
