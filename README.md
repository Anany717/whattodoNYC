# WhatToDo NYC MVP

Context-aware NYC discovery and decision platform.

## Tech Stack
- Frontend: Next.js (App Router) + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: Supabase Postgres (schema in `backend/sql/supabase_schema.sql`)
- Auth: JWT + RBAC
- External APIs: Google Places + AccuWeather (optional keys for MVP)

## Repository Structure
- `backend/` FastAPI service, business logic, tests
- `frontend/` Next.js UI (home, results, map, login/register)
- `backend/sql/supabase_schema.sql` Supabase-compatible schema

## Run Project (Exact Steps)
Use 2 terminal windows: one for backend and one for frontend.

### 1) One-time setup
```bash
cd ~/Desktop/CAPSTONE
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### 2) Backend setup + run (Terminal A)
```bash
cd ~/Desktop/CAPSTONE/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt
sed -i '' 's#^SQLALCHEMY_DATABASE_URL=.*#SQLALCHEMY_DATABASE_URL=sqlite:///./whattodo.db#' .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend:
- Open `http://127.0.0.1:8000/docs`
- Or run:
```bash
curl http://127.0.0.1:8000/health
```
Expected response:
```json
{"status":"ok"}
```

### 3) Seed sample places (optional, recommended)
```bash
cd ~/Desktop/CAPSTONE/backend
source .venv/bin/activate
python -m scripts.seed
```

### 4) Frontend setup + run (Terminal B)
```bash
cd ~/Desktop/CAPSTONE/frontend
npm install
npm run dev
```

Open app:
- `http://localhost:3000`

### 5) Next time you run the project
Backend:
```bash
cd ~/Desktop/CAPSTONE/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:
```bash
cd ~/Desktop/CAPSTONE/frontend
npm run dev
```

## Apply Supabase Schema
Run directly against your Supabase Postgres:
```bash
psql "$SUPABASE_DATABASE_URL" -f backend/sql/supabase_schema.sql
```

## Tests (Backend)
```bash
cd backend
source .venv/bin/activate
pytest tests
```

## Seed Sample Places (10 NYC entries)
```bash
cd backend
source .venv/bin/activate
python -m scripts.seed
```

## API Endpoints
### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Places
- `GET /places/{id}`
- `GET /places/search?query=&lat=&lng=&radius_km=&price_level=&tag=&open_now=`
- `POST /places` (seller/admin)
- `POST /places/{id}/claim` (seller)

### Reviews
- `POST /reviews` (customer/reviewer)
- `GET /places/{id}/reviews`

### Authenticity
- `POST /authenticity/vote` (customer/reviewer)
- `GET /places/{id}/authenticity`

### Promotions
- `POST /promotions` (seller, must own/claim place)
- `GET /places/{id}/promotions`

### Saved Lists
- `POST /saved-lists`
- `POST /saved-lists/{id}/items`
- `GET /saved-lists`

### Recommendations
- `POST /recommendations`

## Curl Examples
Register:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Jane Doe","email":"jane@example.com","password":"strongpass123","role":"customer"}'
```

Login:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"strongpass123"}'
```

Recommendations:
```bash
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "keywords":"cheap authentic thai",
    "budget":2,
    "group_size":3,
    "preference":"indoor",
    "lat":40.7411,
    "lng":-73.9897,
    "radius_km":5
  }'
```

## Notes
- Google Places cache fill runs when candidate count is low and `GOOGLE_PLACES_API_KEY` is set.
- Weather snapshots are cached by 0.02 lat/lng bucket for 30 minutes.
- Recommendation response includes ranking score and concise `why` explanation (top factors).
