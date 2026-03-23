-- =========================================================
-- WhatToDo NYC: Upgrade existing DB enum for current app
-- Run this first, by itself, in Supabase SQL Editor.
-- =========================================================

DO $$
BEGIN
  ALTER TYPE place_source ADD VALUE IF NOT EXISTS 'internal';
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
