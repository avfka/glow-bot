-- Glow Studio: начальная схема
-- Все таблицы защищены RLS: специалист видит и изменяет только свои данные.

create type public.skin_type as enum ('normal', 'dry', 'oily', 'combination', 'sensitive');
create type public.appointment_status as enum ('scheduled', 'done', 'cancelled', 'no_show');
create type public.photo_kind as enum ('before', 'after');
create type public.analysis_source as enum ('text', 'photo');

-- Обновление updated_at
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Специалисты (профиль = auth-пользователь)
-- ---------------------------------------------------------------------------
create table public.specialists (
  id uuid primary key references auth.users (id) on delete cascade,
  telegram_id bigint not null unique,
  name text not null default '',
  specialization text not null default '',
  phone text not null default '',
  avatar_url text,
  onboarded_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.specialists enable row level security;

-- Создание строки выполняет edge function через service role,
-- поэтому insert-политики для клиента нет.
create policy "specialists_select_own" on public.specialists
  for select using (id = auth.uid());

create policy "specialists_update_own" on public.specialists
  for update using (id = auth.uid()) with check (id = auth.uid());

-- ---------------------------------------------------------------------------
-- Клиенты
-- ---------------------------------------------------------------------------
create table public.clients (
  id uuid primary key default gen_random_uuid(),
  specialist_id uuid not null references public.specialists (id) on delete cascade,
  name text not null,
  phone text not null default '',
  telegram_username text not null default '',
  skin_type public.skin_type,
  allergies text not null default '',
  contraindications text not null default '',
  notes text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index clients_specialist_idx on public.clients (specialist_id, name);

create trigger clients_updated_at
  before update on public.clients
  for each row execute function public.set_updated_at();

alter table public.clients enable row level security;

create policy "clients_all_own" on public.clients
  for all using (specialist_id = auth.uid()) with check (specialist_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Услуги
-- ---------------------------------------------------------------------------
create table public.services (
  id uuid primary key default gen_random_uuid(),
  specialist_id uuid not null references public.specialists (id) on delete cascade,
  name text not null,
  duration_min integer not null default 60 check (duration_min > 0),
  price numeric(10, 2) not null default 0 check (price >= 0),
  description text not null default '',
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index services_specialist_idx on public.services (specialist_id, is_active);

alter table public.services enable row level security;

create policy "services_all_own" on public.services
  for all using (specialist_id = auth.uid()) with check (specialist_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Записи
-- ---------------------------------------------------------------------------
create table public.appointments (
  id uuid primary key default gen_random_uuid(),
  specialist_id uuid not null references public.specialists (id) on delete cascade,
  client_id uuid not null references public.clients (id) on delete cascade,
  service_id uuid references public.services (id) on delete set null,
  starts_at timestamptz not null,
  duration_min integer not null default 60 check (duration_min > 0),
  -- снимок цены на момент записи: изменение прайса не должно менять историю
  price numeric(10, 2) not null default 0 check (price >= 0),
  status public.appointment_status not null default 'scheduled',
  note text not null default '',
  remind_before_min integer check (remind_before_min > 0),
  reminded_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index appointments_specialist_starts_idx on public.appointments (specialist_id, starts_at);
create index appointments_client_idx on public.appointments (client_id, starts_at desc);
create index appointments_reminders_idx on public.appointments (starts_at)
  where remind_before_min is not null and reminded_at is null and status = 'scheduled';

create trigger appointments_updated_at
  before update on public.appointments
  for each row execute function public.set_updated_at();

alter table public.appointments enable row level security;

create policy "appointments_all_own" on public.appointments
  for all using (specialist_id = auth.uid()) with check (specialist_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Фото клиентов («до/после»)
-- ---------------------------------------------------------------------------
create table public.client_photos (
  id uuid primary key default gen_random_uuid(),
  specialist_id uuid not null references public.specialists (id) on delete cascade,
  client_id uuid not null references public.clients (id) on delete cascade,
  appointment_id uuid references public.appointments (id) on delete set null,
  kind public.photo_kind not null,
  storage_path text not null,
  taken_at date not null default current_date,
  created_at timestamptz not null default now()
);

create index client_photos_client_idx on public.client_photos (client_id, created_at desc);

alter table public.client_photos enable row level security;

create policy "client_photos_all_own" on public.client_photos
  for all using (specialist_id = auth.uid()) with check (specialist_id = auth.uid());

-- ---------------------------------------------------------------------------
-- AI-разборы составов
-- ---------------------------------------------------------------------------
create table public.ingredient_analyses (
  id uuid primary key default gen_random_uuid(),
  specialist_id uuid not null references public.specialists (id) on delete cascade,
  client_id uuid references public.clients (id) on delete set null,
  source public.analysis_source not null,
  input_text text not null default '',
  result jsonb not null,
  model text not null,
  created_at timestamptz not null default now()
);

create index ingredient_analyses_specialist_idx on public.ingredient_analyses (specialist_id, created_at desc);

alter table public.ingredient_analyses enable row level security;

create policy "ingredient_analyses_all_own" on public.ingredient_analyses
  for all using (specialist_id = auth.uid()) with check (specialist_id = auth.uid());

-- ---------------------------------------------------------------------------
-- Storage: приватный бакет фото клиентов.
-- Путь файла: {specialist_id}/{client_id}/{uuid}.jpg — первый сегмент
-- сверяется с auth.uid() в политиках.
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('client-photos', 'client-photos', false)
on conflict (id) do nothing;

create policy "client_photos_storage_select" on storage.objects
  for select using (
    bucket_id = 'client-photos'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "client_photos_storage_insert" on storage.objects
  for insert with check (
    bucket_id = 'client-photos'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "client_photos_storage_delete" on storage.objects
  for delete using (
    bucket_id = 'client-photos'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
