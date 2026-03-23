# WhatToDo NYC Search Upgrade Plan

Status: completed for this update.

## What Was Investigated
- Frontend search form submission flow from `/` and `/search`
- `GET /places/search` backend route and search service
- Google Places integration and cache/upsert behavior
- Recommendation ranking path
- Search result display in the frontend

## What Was Broken
- The frontend was correctly sending search requests, but the backend was not treating Google Places as the primary search source.
- Live Google search only ran when local matches were below a threshold, so the large seeded catalog prevented external search from running for many realistic queries.
- When Google results were fetched, they were blended back into the same `places` table without enough metadata to make them visible as fresh external results.
- Search results could feel stale because seeded/internal rows and cached rows were hard to distinguish in ranking and UI.
- The schema did not store enough Google metadata to support richer result cards or trustworthy cached external place data.

## Root Cause Analysis
1. Search was effectively local-first because Google fetch was gated behind an “insufficient internal matches” check.
2. Seed data was extensive enough that the fallback threshold often never triggered.
3. Cached Google rows did not carry enough external metadata to feel different from local seed rows.
4. The frontend only showed a generic `google_results_used` message, which hid whether results were actually fresh/live.

## What Changed

### Backend Search Flow
- Reworked `backend/app/services/search_service.py` so keyword searches now attempt live Google Places first.
- Local data is still used for cache, enrichment, fallback, authenticity, promotions, and saved-place continuity.
- Added response metadata for:
  - whether live search was attempted
  - whether it succeeded
  - how many live Google matches were used
  - a product-friendly status message for the UI
- Added per-result source labeling:
  - `live_google`
  - `cached_google`
  - `internal`

### Google Places Integration
- Reworked `backend/app/services/google_places.py` to:
  - support text search with optional location bias
  - fetch Place Details for top results
  - normalize richer fields
  - cache/update results cleanly
  - fail gracefully without crashing the app
- Added better handling for:
  - missing API key
  - request failure
  - zero-result searches
  - dedupe against existing places

### Schema / Data Model Changes
- Extended `places` with external metadata fields:
  - `google_primary_type`
  - `google_rating`
  - `google_user_ratings_total`
  - `external_last_synced_at`
  - `external_raw_json`
  - `is_seed_data`
  - `is_cached_from_external`
- Updated:
  - SQLAlchemy model
  - Pydantic schemas
  - Supabase schema SQL
  - seed logic
  - frontend types

### Ranking Improvements
- Search ranking still prioritizes keyword relevance first.
- Live Google results now get a small tie-break priority so fresh external matches are not buried behind stale local rows.
- Recommendation scoring was updated so keyword relevance is even more dominant.
- Recommendations now also refresh candidates through Google search for keyword-driven requests.

### Frontend Improvements
- Search results now visibly communicate whether live Google search ran and whether fallback was used.
- Result cards and recommendation cards now surface richer external metadata such as:
  - Google-backed badges
  - address
  - Google rating/count where available
- Place detail pages now show:
  - Google-backed data badge
  - Google rating
  - last sync time
  - seed/local catalog badge when relevant

## Files Updated
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/api/routers/places.py`
- `backend/app/services/google_places.py`
- `backend/app/services/search_service.py`
- `backend/app/services/recommendations.py`
- `backend/app/services/place_metrics.py`
- `backend/sql/supabase_schema.sql`
- `backend/scripts/seed.py`
- `backend/tests/test_places_search.py`
- `frontend/lib/types.ts`
- `frontend/components/PlaceCard.tsx`
- `frontend/components/ResultCard.tsx`
- `frontend/components/ResultsClient.tsx`
- `frontend/app/places/[id]/page.tsx`

## Validation
- Backend tests: `pytest tests -q` -> `8 passed`
- Backend Ruff on changed files -> passed
- Frontend lint: `npm run lint` -> passed
- Frontend production build: `npm run build` -> passed

## New Demo Behavior
- Search now feels internet-backed because keyword searches attempt live Google Places first.
- If Google returns fresh results, the UI shows that clearly.
- If Google is unavailable, the app falls back to cached/local results with a user-friendly message.
- External results are stored with richer metadata for reuse in later searches and place detail views.

## Future Work
- Add freshness TTL rules so cached external places can be selectively refreshed by age.
- Add background sync / search analytics if needed for a larger demo.
- Add pagination or infinite scroll for broader search result sets.
- Add Google opening-hours enrichment if more detailed live availability becomes important.
