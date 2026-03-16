# WhatToDo NYC

Context-aware discovery and decision platform for NYC.

This repo now includes the next milestone features:
- Place detail pages with reviews/authenticity/promotions/actions
- User profile + saved lists + dashboard views
- Seller dashboard + promotion creation
- Admin dashboard scaffold
- Role-based protected frontend routes and backend RBAC endpoints

## Stack
- Frontend: Next.js App Router + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: Supabase Postgres (schema file included) or SQLite for local quick run
- Auth: JWT + role-based access control (`customer`, `reviewer`, `seller`, `admin`)

## Project Structure
- `backend/` FastAPI app, routers, services, tests, seed script
- `frontend/` Next.js app, components, auth/API utilities
- `backend/sql/supabase_schema.sql` Supabase-compatible schema
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

## Optional: Seed 10 NYC Places

```bash
cd ~/Desktop/CAPSTONE/backend
source .venv/bin/activate
python -m scripts.seed
```

## Optional: Apply Supabase Schema

```bash
psql "$SUPABASE_DATABASE_URL" -f backend/sql/supabase_schema.sql
```

## Frontend Routes

Public:
- `/`
- `/login`
- `/register`
- `/places/[id]`
- `/results`
- `/map`

Protected:
- `/profile`
- `/dashboard`
- `/saved-lists`
- `/seller/dashboard` (seller only)
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

### Authenticity
- `POST /authenticity/vote` (upsert by user/place)

### Saved Lists
- `POST /saved-lists`
- `GET /saved-lists`
- `POST /saved-lists/{id}/items`
- `DELETE /saved-lists/{id}/items/{place_id}`

### Seller
- `GET /seller/places`
- `GET /seller/promotions`
- `POST /promotions`

### Admin (scaffold)
- `GET /admin/users`
- `GET /admin/places`

### Recommendations
- `POST /recommendations`

## Demo Flows
1. Register and login (`customer` or `reviewer`).
2. Open `/profile` and verify account info + reviews + saved lists preview.
3. Open `/places/{id}` and:
   - submit or edit a review
   - vote authentic/touristy
   - save place
4. Open `/saved-lists` and verify list/item state updates.
5. Login as `seller` and use `/seller/dashboard` to create a promotion.
6. Login as `admin` and open `/admin/dashboard`.
7. Verify unauthorized access behavior for seller/admin pages.

## Quality Checks

Backend tests:

```bash
cd backend
source .venv/bin/activate
pytest tests
```

Frontend lint/build:

```bash
cd frontend
npm run lint
npm run build
```

## Notes
- Set `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to enable map markers.
- Set `GOOGLE_PLACES_API_KEY` and `ACCUWEATHER_API_KEY` in `backend/.env` to enable external enrichment.
- No secrets should be committed.
