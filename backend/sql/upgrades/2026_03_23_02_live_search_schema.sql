-- =========================================================
-- WhatToDo NYC: Upgrade existing DB for live-search metadata
-- Run this after 2026_03_23_01_add_internal_place_source.sql
-- Safe for an already-initialized project database.
-- =========================================================

ALTER TABLE places
  ADD COLUMN IF NOT EXISTS google_primary_type TEXT,
  ADD COLUMN IF NOT EXISTS google_rating DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS google_user_ratings_total INTEGER,
  ADD COLUMN IF NOT EXISTS external_last_synced_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS external_raw_json JSONB,
  ADD COLUMN IF NOT EXISTS is_seed_data BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS is_cached_from_external BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE places
  ALTER COLUMN source SET DEFAULT 'internal';

ALTER TABLE places
  ALTER COLUMN place_type SET DEFAULT 'restaurant';

UPDATE places
SET source = 'internal'
WHERE source::text IN ('seller', 'seed');

UPDATE places
SET is_seed_data = true
WHERE source::text = 'internal'
  AND managed_by_user_id IS NULL
  AND is_seed_data = false;

CREATE INDEX IF NOT EXISTS idx_places_source
  ON places(source);

CREATE INDEX IF NOT EXISTS idx_places_external_last_synced_at
  ON places(external_last_synced_at);
