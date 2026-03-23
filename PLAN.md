# WhatToDo NYC Upgrade Plan

Status: completed for this phase. Backend and frontend are now aligned with the upgraded search, profile, review, and saved-list flows.

## Phase 1: Audit Findings
- Existing auth, recommendations, place detail, reviews, authenticity, saved-list, seller, and admin scaffolding are already in place.
- Current saved-place UX already uses heart/bookmark controls and should be preserved.
- Search currently works for local data and has a basic Google Places fallback, but it is still route-centric, lacks a dedicated search service, and does not support `sort_by`.
- Google Places integration currently only performs a simple text search call and caches unseen places by `google_place_id`; error handling is safe but normalization and merge/dedupe logic need to be stronger.
- Recommendations already incorporate reviews, authenticity, distance, weather, and promotions, but keyword relevance is not yet dominant enough.
- Missing or incomplete backend endpoints for this phase:
  - `GET /users/me/saved-lists`
  - `GET /saved-lists/{id}`
  - `DELETE /reviews/{id}`
  - `GET /admin/reviews`
- Frontend currently has `/`, `/results`, `/places/[id]`, `/profile`, `/saved-lists`, seller/admin dashboards, and protected route handling, but it still needs:
  - a stronger homepage/search flow with sorting
  - dedicated `/search`
  - saved-list detail page
  - tighter integration with updated search/sort backend responses

## Phase 2: Backend Core
- Add a dedicated search service for filtering, ranking, dedupe, and sorting.
- Strengthen Google Places fetch + normalization + caching behavior.
- Add `sort_by` support to `/places/search`.
- Expand place detail support through consistent aggregates and related route coverage.
- Complete reviews, saved-lists, profile, and admin endpoints.

## Phase 3: Data Alignment
- Keep the current schema unless implementation proves a schema change is necessary.
- Update Pydantic schemas, frontend types, seed assumptions, and README to reflect any API shape changes.

## Phase 4: Frontend Foundation
- Update shared API utilities and types for new search and profile/list endpoints.
- Add shared search/sort components where needed.
- Preserve the existing navbar, protected-route logic, and favorites/list save UX.

## Phase 5: Frontend Pages
- Upgrade homepage into a stronger search landing experience.
- Add `/search` and `/saved-lists/[id]`.
- Improve `/places/[id]`, `/profile`, seller/admin dashboards, and saved-lists flows with the real backend data.

## Phase 6: Integration + QA
- Validate search -> place detail -> save/review flows.
- Validate profile + saved-lists + role dashboards.
- Run backend tests, frontend lint/build, and update README with current behavior.

## Validation Completed
- Backend tests: `pytest tests` -> passing (`6 passed`)
- Backend scoped Ruff on changed files -> passing
- Frontend lint: `npm run lint` -> passing
- Frontend production build: `npm run build` -> passing
