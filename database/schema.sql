create table if not exists public.creators (
  id                 text primary key,
  name               text not null,
  handle             text,
  location           text,
  joined             text,
  bio                text,
  specialization     text,
  workflow           text,
  niches             text[]  default '{}',
  skills             text[]  default '{}',
  tools              text[]  default '{}',
  content_types      text[]  default '{}',
  formats            text[]  default '{}',
  followers          text,
  engagement         text,
  avg_views          text,
  rate_min           integer,
  rate_max           integer,
  turnaround_days    integer,
  commercial_license boolean default true,
  verified_tools     text[]  default '{}',
  verified_past_work boolean default false,
  rating             numeric(2,1),
  avatar             text,
  banner             text,
  recent_work        text[]  default '{}'
);

alter table public.creators enable row level security;

create policy "Public can read creators"
  on public.creators for select
  to anon
  using (true);

  alter table public.creators
  add column if not exists portfolio jsonb default '[]'::jsonb,
  add column if not exists verified_workflow boolean default false,
  add column if not exists process_evidence text;