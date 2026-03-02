-- WhatToDo NYC Supabase schema (Postgres)
create extension if not exists pgcrypto;

create type user_role as enum ('customer','reviewer','seller','admin');
create type place_source as enum ('google','internal');
create type place_type as enum ('restaurant','event','activity');
create type authenticity_label as enum ('authentic','touristy');

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  email text not null unique,
  password_hash text not null,
  role user_role not null,
  created_at timestamptz not null default now()
);

create table if not exists places (
  id uuid primary key default gen_random_uuid(),
  google_place_id text unique,
  source place_source not null,
  place_type place_type not null,
  name text not null,
  formatted_address text,
  neighborhood text,
  lat double precision not null,
  lng double precision not null,
  price_level integer check (price_level between 1 and 4),
  phone text,
  website text,
  managed_by_user_id uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists place_hours (
  id uuid primary key default gen_random_uuid(),
  place_id uuid not null references places(id) on delete cascade,
  day_of_week smallint not null check (day_of_week between 0 and 6),
  open_time time,
  close_time time,
  is_closed boolean not null default false,
  unique(place_id, day_of_week)
);

create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  place_id uuid not null references places(id) on delete cascade,
  rating_overall smallint not null check (rating_overall between 1 and 5),
  rating_value smallint check (rating_value between 1 and 5),
  rating_vibe smallint check (rating_vibe between 1 and 5),
  rating_groupfit smallint check (rating_groupfit between 1 and 5),
  comment text,
  created_at timestamptz not null default now(),
  unique(user_id, place_id)
);

create table if not exists authenticity_votes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  place_id uuid not null references places(id) on delete cascade,
  label authenticity_label not null,
  created_at timestamptz not null default now(),
  unique(user_id, place_id)
);

create table if not exists tags (
  id uuid primary key default gen_random_uuid(),
  name text not null unique
);

create table if not exists place_tags (
  place_id uuid not null references places(id) on delete cascade,
  tag_id uuid not null references tags(id) on delete cascade,
  primary key(place_id, tag_id)
);

create table if not exists promotions (
  id uuid primary key default gen_random_uuid(),
  place_id uuid not null references places(id) on delete cascade,
  seller_user_id uuid not null references users(id) on delete cascade,
  title text not null,
  description text,
  boost_factor numeric(3,2) not null check (boost_factor >= 1.00 and boost_factor <= 3.00),
  start_at timestamptz not null,
  end_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists weather_snapshots (
  id uuid primary key default gen_random_uuid(),
  lat_bucket double precision not null,
  lng_bucket double precision not null,
  fetched_at timestamptz not null default now(),
  data_json jsonb not null
);

create table if not exists saved_lists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  unique(user_id, name)
);

create table if not exists saved_list_items (
  list_id uuid not null references saved_lists(id) on delete cascade,
  place_id uuid not null references places(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(list_id, place_id)
);
