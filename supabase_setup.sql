
create extension if not exists pgcrypto;

create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  session_id text unique not null,
  data jsonb,
  created_at timestamptz default now()
);

create table if not exists interactions (
  id uuid primary key default gen_random_uuid(),
  customer_id text not null,
  recommendations jsonb,
  approved boolean default false,
  feedback text default '',
  created_at timestamptz default now()
);

create index if not exists idx_interactions_customer_id on interactions (customer_id);
