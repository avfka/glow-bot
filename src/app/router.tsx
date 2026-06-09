import { Route, Routes } from 'react-router-dom';

import { AnalyzerPage } from '@/features/analyzer/AnalyzerPage';
import { AppointmentFormPage } from '@/features/appointments/AppointmentFormPage';
import { AppointmentsPage } from '@/features/appointments/AppointmentsPage';
import { ClientFormPage } from '@/features/clients/ClientFormPage';
import { ClientPage } from '@/features/clients/ClientPage';
import { ClientsPage } from '@/features/clients/ClientsPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { ProfilePage } from '@/features/onboarding/ProfilePage';
import { ServicesPage } from '@/features/services/ServicesPage';

import { AppShell } from './AppShell';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="appointments" element={<AppointmentsPage />} />
        <Route path="appointments/new" element={<AppointmentFormPage />} />
        <Route path="appointments/:id/edit" element={<AppointmentFormPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="clients/new" element={<ClientFormPage />} />
        <Route path="clients/:id" element={<ClientPage />} />
        <Route path="clients/:id/edit" element={<ClientFormPage />} />
        <Route path="services" element={<ServicesPage />} />
        <Route path="analyzer" element={<AnalyzerPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
    </Routes>
  );
}
