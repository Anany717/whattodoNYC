# WhatToDo NYC

Context-aware discovery and decision platform for NYC.

This repo now includes the next milestone features:
- Place detail pages with reviews/authenticity/promotions/actions
- User profile + saved lists + dashboard views
- Seller dashboard + promotion creation
- Admin dashboard scaffold
- Role-based protected frontend routes and backend RBAC endpoints
- Keyword-first search with sort options and Google Places fallback/cache
- Saved-list favorites/bookmark UX and saved-list detail pages

## Stack
- Frontend: Next.js App Router + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: Supabase Postgres (schema file included) or SQLite for local quick run
- Auth: JWT + role-based access control (`customer`, `reviewer`, `seller`, `admin`)

## Project Structure
- `backend/` FastAPI app, routers, services, tests, seed script
- `frontend/` Next.js app, components, auth/API utilities
- `backend/sql/supabase_schema.sql` fresh Supabase/Postgres schema
- `backend/sql/upgrades/` incremental upgrade SQL for existing databases
- `PLAN.md` milestone implementation plan and status

## Environment Setup
From repo root:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

## Run Locally
Use two terminals.

### Terminal A: Backend

```bash
cd ~/Desktop/CAPSTONE/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt

# Optional for local-only demo without Postgres/Supabase
sed -i '' 's#^SQLALCHEMY_DATABASE_URL=.*#SQLALCHEMY_DATABASE_URL=sqlite:///./whattodo.db#' .env

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify:
- `http://127.0.0.1:8000/docs`
- `curl http://127.0.0.1:8000/health`

### Terminal B: Frontend

```bash
cd ~/Desktop/CAPSTONE/frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

## Optional: Seed Demo Data

```bash
cd ~/Desktop/CAPSTONE/backend
source .venv/bin/activate
python -m scripts.seed
```

Seed highlights:
- 50 demo places total
- 30 restaurants
- 10 events
- 10 activities
- seeded demo admin login:
  - `admin@whattodonyc.local`
  - `AdminDemo123!`

## Database Schema

### Fresh Supabase / Postgres Setup

```bash
psql "$SUPABASE_DATABASE_URL" -f backend/sql/supabase_schema.sql
```

### Upgrade Existing Supabase / Postgres Database

Run these in order:

```bash
psql "$SUPABASE_DATABASE_URL" -f backend/sql/upgrades/2026_03_23_01_add_internal_place_source.sql
psql "$SUPABASE_DATABASE_URL" -f backend/sql/upgrades/2026_03_23_02_live_search_schema.sql
```

This upgrade path adds the live-search metadata used by the current app:
- `google_primary_type`
- `google_rating`
- `google_user_ratings_total`
- `external_last_synced_at`
- `external_raw_json`
- `is_seed_data`
- `is_cached_from_external`

It only alters the existing `places` table and adds supporting indexes, so it is safe for a database that already has the original project tables.

### Local SQLite Demo Database

Local SQLite is good for fast development, but it will not auto-migrate older files.
If your local `whattodo.db` is behind the current model shape, reset and reseed it:

```bash
cd backend
mv whattodo.db whattodo.db.bak 2>/dev/null || true
source .venv/bin/activate
python -m scripts.seed
```

## Frontend Routes

Public:
- `/`
- `/login`
- `/register`
- `/search`
- `/places/[id]`
- `/results`
- `/map`

Protected:
- `/profile`
- `/dashboard`
- `/saved-lists`
- `/saved-lists/[id]`
- `/seller/dashboard` (seller/admin)
- `/admin/dashboard` (admin only)

Route behavior:
- No token: redirect to `/login`
- Wrong role: access denied state

## Backend API Summary

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Users/Profile
- `GET /users/me`
- `PUT /users/me`
- `GET /users/me/reviews`
- `GET /users/me/saved-lists`

### Places
- `GET /places/{id}`
- `GET /places/search`
- `POST /places` (seller/admin)
- `POST /places/{id}/claim` (seller)
- `GET /places/{id}/reviews`
- `GET /places/{id}/authenticity`
- `GET /places/{id}/promotions`

### Reviews
- `POST /reviews` (upsert by user/place)
- `PUT /reviews/{id}`
- `DELETE /reviews/{id}`

### Authenticity
- `POST /authenticity/vote` (upsert by user/place)

### Saved Lists
- `POST /saved-lists`
- `GET /saved-lists`
- `GET /saved-lists/{id}`
- `POST /saved-lists/{id}/items`
- `DELETE /saved-lists/{id}/items/{place_id}`

### Seller
- `GET /seller/places`
- `GET /seller/promotions`
- `POST /promotions`

### Admin (scaffold)
- `GET /admin/users`
- `GET /admin/places`
- `GET /admin/reviews`

### Recommendations
- `POST /recommendations`

## Search Behavior
- Keyword searches now attempt live Google Places first.
- Live Google results are normalized into the internal place shape, cached in the database, and deduplicated against near-identical existing places.
- Local places are still used for enrichment, fallback, reviews, authenticity, promotions, and saved-list continuity.
- Search responses now tell the frontend whether:
  - live search was attempted
  - live search succeeded
  - live Google matches were used
- Places store richer external metadata, including Google ratings and last sync time, so cached results still feel dynamic after the first fetch.
- Search supports:
  - `relevance`
  - `price_asc`
  - `price_desc`
  - `rating_desc`
  - `distance_asc`
  - `authenticity_desc`
- Keyword relevance is the strongest ranking factor in both `/places/search` and `/recommendations`.

## Demo Flows
1. Register and login (`customer` or `reviewer`).
2. Open `/search`, run a keyword search, and verify:
   - recommendation cards
   - sorted search results
   - saved heart/bookmark actions
3. Open `/places/{id}` and:
   - submit or edit a review
   - vote authentic/touristy
   - save place
4. Open `/saved-lists` and `/saved-lists/{id}` and verify list/item state updates.
5. Open `/profile` and verify account info + reviews + saved lists + saved places preview.
6. Login as `seller` and use `/seller/dashboard` to create a place and then a promotion.
7. Login as `admin` and open `/admin/dashboard`.
8. Verify unauthorized access behavior for seller/admin pages.

## Quality Checks

Backend tests:

```bash
cd backend
source .venv/bin/activate
pytest tests
```

Backend Ruff on changed files:

```bash
cd backend
source .venv/bin/activate
ruff check app/api/routers/admin.py app/api/routers/places.py app/api/routers/promotions.py app/api/routers/reviews.py app/api/routers/saved_lists.py app/api/routers/seller.py app/api/routers/users.py app/schemas.py app/services/google_places.py app/services/place_metrics.py app/services/recommendations.py app/services/search_service.py tests/test_places_search.py tests/test_profile_saved_lists.py
```

Frontend lint/build:

```bash
cd frontend
npm run lint
npm run build
```

## Notes
- Set `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to enable map markers.
- Set `GOOGLE_PLACES_API_KEY` in `backend/.env` to enable live Google-backed search.
- Set `ACCUWEATHER_API_KEY` in `backend/.env` to enable live weather enrichment.
- If `GOOGLE_PLACES_API_KEY` is missing or Google is temporarily unavailable, the app falls back to cached/local results without crashing.
- No secrets should be committed.
