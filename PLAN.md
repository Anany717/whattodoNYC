# WhatToDo NYC Milestone Plan

## Phase 1: Audit + Alignment (Completed)
- Confirmed backend already had core auth/place/review/authenticity/saved-list/promotions routes.
- Confirmed frontend had landing/results/map/login/register and needed milestone expansion.
- Identified gaps: place detail, profile/dashboard experiences, protected/role routes, and missing backend user/seller/admin endpoints.

## Phase 2: Backend API Completion (Completed)
- Added `PUT /reviews/{id}`.
- Added profile/user endpoints: `GET /users/me`, `PUT /users/me`, `GET /users/me/reviews`.
- Added role scaffold endpoints:
  - `GET /seller/places`
  - `GET /seller/promotions`
  - `GET /admin/users`
  - `GET /admin/places`
- Added `DELETE /saved-lists/{id}/items/{place_id}`.
- Expanded `GET /places/{id}` response with tags, average rating, authenticity score, and review count.

## Phase 3: Shared Frontend Utilities + Components (Completed)
- Expanded `frontend/lib/types.ts` for role-aware and page-specific data types.
- Expanded `frontend/lib/api.ts` for all milestone endpoints.
- Added `frontend/lib/auth.ts` for token storage, current-user loading, and role checks.
- Added reusable components:
  - `Navbar`
  - `ProtectedRoute`
  - `PlaceCard`
  - `ReviewCard`
  - `ReviewForm`
  - `ProfileHeader`
  - `RoleBadge`
  - `SavedListCard`
  - `SellerStatsCard`
  - `EmptyState`

## Phase 4: Place Detail + Reviews UX (Completed)
- Added `app/places/[id]/page.tsx`.
- Implemented place info, ratings/authenticity summary, active promotions, and reviews list.
- Implemented logged-in actions:
  - Write or edit review
  - Vote authentic/touristy
  - Save place to a list

## Phase 5: Profile + Saved Lists + Dashboards (Completed)
- Added `app/profile/page.tsx` with account details, role badge, profile edit form, reviews, and saved lists.
- Added `app/saved-lists/page.tsx` with create/add/remove list item flows.
- Added `app/dashboard/page.tsx` as role-aware dashboard hub.
- Added `app/seller/dashboard/page.tsx` with managed places, promotions, stats, and promotion creation form.
- Added `app/admin/dashboard/page.tsx` scaffold with aggregate stats and list placeholders.

## Phase 6: Navigation + Route Protection + Home Flow (Completed)
- Replaced static header with role-aware `Navbar`.
- Added protected route handling for:
  - `/profile`
  - `/dashboard`
  - `/saved-lists`
  - `/seller/dashboard`
  - `/admin/dashboard`
- Enforced role-based access deny behavior for seller/admin sections.
- Refreshed homepage hero + search flow.

## Phase 7: End-to-End Validation (Completed)
- Validated build + runtime integration paths in code for:
  - register -> login -> profile
  - place detail -> review create/update -> review list refresh
  - authenticity vote -> summary refresh
  - saved list add/remove flows
  - seller dashboard data + promotion creation
  - role-protected route behavior

## Phase 8: Polish + Documentation (Completed)
- Unified UI into a neutral, card-based, consistent layout.
- Removed developer-facing strings from key user pages.
- Ran backend tests + frontend lint/build and resolved issues.
- Updated README with setup, routes, role matrix, and demo checklist.
