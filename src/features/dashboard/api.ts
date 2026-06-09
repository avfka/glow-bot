import { useQuery } from '@tanstack/react-query';
import { endOfWeek, startOfMonth, startOfWeek } from 'date-fns';

import { supabase } from '@/lib/supabase';

export interface DashboardStats {
  clientsCount: number;
  weekAppointments: number;
  monthRevenue: number;
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async (): Promise<DashboardStats> => {
      const now = new Date();
      const weekStart = startOfWeek(now, { weekStartsOn: 1 }).toISOString();
      const weekEnd = endOfWeek(now, { weekStartsOn: 1 }).toISOString();
      const monthStart = startOfMonth(now).toISOString();

      const [clientsRes, weekRes, revenueRes] = await Promise.all([
        supabase.from('clients').select('id', { count: 'exact', head: true }),
        supabase
          .from('appointments')
          .select('id', { count: 'exact', head: true })
          .gte('starts_at', weekStart)
          .lte('starts_at', weekEnd)
          .neq('status', 'cancelled'),
        supabase
          .from('appointments')
          .select('price')
          .eq('status', 'done')
          .gte('starts_at', monthStart),
      ]);

      if (clientsRes.error) throw clientsRes.error;
      if (weekRes.error) throw weekRes.error;
      if (revenueRes.error) throw revenueRes.error;

      return {
        clientsCount: clientsRes.count ?? 0,
        weekAppointments: weekRes.count ?? 0,
        monthRevenue: revenueRes.data.reduce((sum, row) => sum + Number(row.price), 0),
      };
    },
  });
}
