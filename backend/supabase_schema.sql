-- Sofa Genius — Supabase schema migration
-- Run this in the Supabase SQL Editor after creating the project.

-- 1. Profiles (extends auth.users) ----------------------------------------

create table public.profiles (
  id          uuid primary key references auth.users on delete cascade,
  display_name text,
  email       text,
  avatar_url  text,
  wandb_api_key text,
  wandb_entity  text,
  hf_token    text,
  hf_username text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

-- Auto-create profile on sign-up
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, display_name, email, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name', ''),
    new.email,
    coalesce(new.raw_user_meta_data ->> 'avatar_url', '')
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 2. Sessions -------------------------------------------------------------

create table public.sessions (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles on delete cascade,
  title      text not null default 'New Chat',
  preview    text default '',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.sessions enable row level security;

create policy "Users can view own sessions"
  on public.sessions for select
  using (auth.uid() = user_id);

create policy "Users can insert own sessions"
  on public.sessions for insert
  with check (auth.uid() = user_id);

create policy "Users can update own sessions"
  on public.sessions for update
  using (auth.uid() = user_id);

create policy "Users can delete own sessions"
  on public.sessions for delete
  using (auth.uid() = user_id);

-- 3. Messages -------------------------------------------------------------

create table public.messages (
  id         uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions on delete cascade,
  role       text not null check (role in ('user', 'assistant')),
  content    text not null default '',
  segments   jsonb,
  created_at timestamptz default now()
);

alter table public.messages enable row level security;

create policy "Users can view own messages"
  on public.messages for select
  using (
    exists (
      select 1 from public.sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

create policy "Users can insert own messages"
  on public.messages for insert
  with check (
    exists (
      select 1 from public.sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

-- 4. Cards ----------------------------------------------------------------

create table public.cards (
  id         uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions on delete cascade,
  card_type  text not null,
  title      text not null default '',
  data       jsonb not null default '{}',
  created_at timestamptz default now()
);

alter table public.cards enable row level security;

create policy "Users can view own cards"
  on public.cards for select
  using (
    exists (
      select 1 from public.sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

create policy "Users can insert own cards"
  on public.cards for insert
  with check (
    exists (
      select 1 from public.sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

-- 5. Auto-update triggers -------------------------------------------------

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

create trigger sessions_updated_at
  before update on public.sessions
  for each row execute function public.set_updated_at();

-- 6. Indexes --------------------------------------------------------------

create index sessions_user_id_idx on public.sessions (user_id, updated_at desc);
create index messages_session_id_idx on public.messages (session_id, created_at);
create index cards_session_id_idx on public.cards (session_id, created_at);
