-- =========================================================
-- WhatToDo NYC: Supabase / PostgreSQL Schema
-- Fresh database setup
-- =========================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -------------------------
-- ENUM TYPES
-- -------------------------
DO $$
BEGIN
  CREATE TYPE user_role AS ENUM ('customer', 'reviewer', 'seller', 'admin');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE place_source AS ENUM ('google', 'internal');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE place_type AS ENUM ('restaurant', 'event', 'activity');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE authenticity_label AS ENUM ('authentic', 'touristy');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE friendship_status AS ENUM ('pending', 'accepted', 'declined', 'blocked');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE plan_status AS ENUM ('draft', 'active', 'finalized', 'archived');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE plan_visibility AS ENUM ('private', 'shared');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE plan_member_role AS ENUM ('host', 'collaborator');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
  CREATE TYPE plan_vote_value AS ENUM ('yes', 'no', 'maybe');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

-- -------------------------
-- USERS
-- -------------------------
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'customer',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -------------------------
-- PLACES
-- -------------------------
CREATE TABLE IF NOT EXISTS places (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  google_place_id TEXT UNIQUE,
  google_primary_type TEXT,
  google_rating DOUBLE PRECISION,
  google_user_ratings_total INTEGER,
  source place_source NOT NULL DEFAULT 'internal',
  place_type place_type NOT NULL DEFAULT 'restaurant',
  name TEXT NOT NULL,
  formatted_address TEXT,
  neighborhood TEXT,
  lat DOUBLE PRECISION NOT NULL,
  lng DOUBLE PRECISION NOT NULL,
  price_level INTEGER CHECK (price_level BETWEEN 1 AND 4),
  phone TEXT,
  website TEXT,
  external_last_synced_at TIMESTAMPTZ,
  external_raw_json JSONB,
  is_seed_data BOOLEAN NOT NULL DEFAULT false,
  is_cached_from_external BOOLEAN NOT NULL DEFAULT false,
  managed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_places_type ON places(place_type);
CREATE INDEX IF NOT EXISTS idx_places_neighborhood ON places(neighborhood);
CREATE INDEX IF NOT EXISTS idx_places_lat_lng ON places(lat, lng);
CREATE INDEX IF NOT EXISTS idx_places_source ON places(source);
CREATE INDEX IF NOT EXISTS idx_places_external_last_synced_at ON places(external_last_synced_at);

-- -------------------------
-- PLACE HOURS
-- -------------------------
CREATE TABLE IF NOT EXISTS place_hours (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
  open_time TIME,
  close_time TIME,
  is_closed BOOLEAN NOT NULL DEFAULT false,
  CONSTRAINT closed_requires_null_times CHECK (
    (is_closed = true AND open_time IS NULL AND close_time IS NULL)
    OR (is_closed = false)
  )
);

CREATE INDEX IF NOT EXISTS idx_place_hours_place_id ON place_hours(place_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_place_hours_place_day ON place_hours(place_id, day_of_week);

-- -------------------------
-- REVIEWS
-- -------------------------
CREATE TABLE IF NOT EXISTS reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  rating_overall SMALLINT NOT NULL CHECK (rating_overall BETWEEN 1 AND 5),
  rating_value SMALLINT CHECK (rating_value BETWEEN 1 AND 5),
  rating_vibe SMALLINT CHECK (rating_vibe BETWEEN 1 AND 5),
  rating_groupfit SMALLINT CHECK (rating_groupfit BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reviews_place_id ON reviews(place_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reviews_user_place ON reviews(user_id, place_id);

-- -------------------------
-- AUTHENTICITY VOTES
-- -------------------------
CREATE TABLE IF NOT EXISTS authenticity_votes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  label authenticity_label NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_votes_place_id ON authenticity_votes(place_id);
CREATE INDEX IF NOT EXISTS idx_auth_votes_user_id ON authenticity_votes(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_votes_user_place ON authenticity_votes(user_id, place_id);

-- -------------------------
-- TAGS + PLACE TAGS
-- -------------------------
CREATE TABLE IF NOT EXISTS tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS place_tags (
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (place_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_place_tags_place_id ON place_tags(place_id);
CREATE INDEX IF NOT EXISTS idx_place_tags_tag_id ON place_tags(tag_id);

-- -------------------------
-- PROMOTIONS
-- -------------------------
CREATE TABLE IF NOT EXISTS promotions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  seller_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  boost_factor NUMERIC(3,2) NOT NULL DEFAULT 1.00
    CHECK (boost_factor >= 1.00 AND boost_factor <= 3.00),
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT promo_time_valid CHECK (end_at > start_at)
);

CREATE INDEX IF NOT EXISTS idx_promotions_place_id ON promotions(place_id);
CREATE INDEX IF NOT EXISTS idx_promotions_seller_id ON promotions(seller_user_id);
CREATE INDEX IF NOT EXISTS idx_promotions_active ON promotions(start_at, end_at);

-- -------------------------
-- WEATHER SNAPSHOTS
-- -------------------------
CREATE TABLE IF NOT EXISTS weather_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lat_bucket DOUBLE PRECISION NOT NULL,
  lng_bucket DOUBLE PRECISION NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  data_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weather_bucket ON weather_snapshots(lat_bucket, lng_bucket);
CREATE INDEX IF NOT EXISTS idx_weather_fetched_at ON weather_snapshots(fetched_at);

-- -------------------------
-- SAVED LISTS
-- -------------------------
CREATE TABLE IF NOT EXISTS saved_lists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_lists_user_name ON saved_lists(user_id, name);

CREATE TABLE IF NOT EXISTS saved_list_items (
  list_id UUID NOT NULL REFERENCES saved_lists(id) ON DELETE CASCADE,
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (list_id, place_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_items_place_id ON saved_list_items(place_id);
CREATE INDEX IF NOT EXISTS idx_saved_items_list_id ON saved_list_items(list_id);

-- -------------------------
-- FRIENDSHIPS
-- -------------------------
CREATE TABLE IF NOT EXISTS friendships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  addressee_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status friendship_status NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (requester_user_id <> addressee_user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_friendships_direction
  ON friendships(requester_user_id, addressee_user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_requester
  ON friendships(requester_user_id, status);
CREATE INDEX IF NOT EXISTS idx_friendships_addressee
  ON friendships(addressee_user_id, status);

-- -------------------------
-- PLANS
-- -------------------------
CREATE TABLE IF NOT EXISTS plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  status plan_status NOT NULL DEFAULT 'draft',
  visibility plan_visibility NOT NULL DEFAULT 'shared',
  final_place_id UUID REFERENCES places(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_plans_host_status
  ON plans(host_user_id, status);
CREATE INDEX IF NOT EXISTS idx_plans_final_place
  ON plans(final_place_id);

CREATE TABLE IF NOT EXISTS plan_members (
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role plan_member_role NOT NULL DEFAULT 'collaborator',
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (plan_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_plan_members_user
  ON plan_members(user_id);

CREATE TABLE IF NOT EXISTS plan_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
  place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  added_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_items_plan_place
  ON plan_items(plan_id, place_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_plan
  ON plan_items(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_place
  ON plan_items(place_id);

CREATE TABLE IF NOT EXISTS plan_item_votes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_item_id UUID NOT NULL REFERENCES plan_items(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  vote plan_vote_value NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_item_votes_item_user
  ON plan_item_votes(plan_item_id, user_id);
CREATE INDEX IF NOT EXISTS idx_plan_item_votes_item
  ON plan_item_votes(plan_item_id);
CREATE INDEX IF NOT EXISTS idx_plan_item_votes_user
  ON plan_item_votes(user_id);
