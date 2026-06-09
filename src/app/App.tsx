import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HashRouter } from 'react-router-dom';

import { useThemeSync } from '@/hooks/useThemeSync';

import { AuthGate } from './AuthGate';
import { NotInTelegram } from './NotInTelegram';
import { AppRoutes } from './router';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

interface AppProps {
  inTelegram: boolean;
}

export function App({ inTelegram }: AppProps) {
  useThemeSync();

  if (!inTelegram) {
    return <NotInTelegram />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      {/* HashRouter — чтобы приложение переживало перезагрузку на любом статическом хостинге */}
      <HashRouter>
        <AuthGate>
          <AppRoutes />
        </AuthGate>
      </HashRouter>
    </QueryClientProvider>
  );
}
