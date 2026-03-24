# WhatToDo NYC Collaborative Plans Plan

Status: implemented for this update.

## Audit Findings
- `saved_lists` currently support only private bookmarking and do not model collaboration, membership, or voting.
- Auth, users, and place search flows already exist and are stable enough to reuse.
- Place search already normalizes Google-backed results into `places`, which means plan items can reuse `place_id` without adding a second external-candidate model.
- The cleanest path is to keep private saved lists intact and add first-class collaborative planning tables and routes beside them.

## Product Direction
- Keep `saved_lists` as lightweight private organization.
- Add social planning as a separate feature built around `plans`.
- Support an in-app friends graph so plans feel native and collaborative rather than link-only sharing.
- Reuse existing place search and place detail infrastructure for adding restaurant/activity candidates into a plan.

## Data Model Changes
- Add `friendships` for requests and accepted friend relationships.
- Add `plans` for host-owned collaborative plans.
- Add `plan_members` for membership and roles.
- Add `plan_items` for candidate places/events attached to a plan.
- Add `plan_item_votes` for yes/no/maybe voting with one vote per member per item.
- Keep `saved_lists` and `saved_list_items` unchanged for private lists.
- Add new SQL enum types:
  - `friendship_status`
  - `plan_status`
  - `plan_visibility`
  - `plan_member_role`
  - `plan_vote_value`
- Update fresh schema in `backend/sql/supabase_schema.sql`.
- Add additive upgrade script in `backend/sql/upgrades/2026_03_24_01_collaborative_plans.sql`.

## Backend Changes
- Add friends routes for search, request, accept, decline, list, and remove.
- Add plans routes for create, read, update, invite, membership, item management, voting, summary, and finalization.
- Add helper service logic to compute vote totals, leading option, and final choice.
- Enforce permissions:
  - auth required for all social features
  - only plan members can view a plan
  - only host can invite/remove/finalize
  - any member can vote
- New backend files:
  - `backend/app/api/routers/friends.py`
  - `backend/app/api/routers/plans.py`
  - `backend/app/services/plans.py`
- Existing backend files updated:
  - `backend/app/models.py`
  - `backend/app/schemas.py`
  - `backend/app/api/router.py`

## Frontend Changes
- Add `/friends`, `/plans`, `/plans/new`, and `/plans/[id]`.
- Add plan index, plan detail, and create-plan flows.
- Add friends management UI with search, requests, and accepted friends.
- Add voting controls, member list, final-choice banner, and add-to-plan search flow.
- Update navbar/navigation to surface plans and friends.
- New reusable UI components:
  - `PlanCard`
  - `PlanMemberList`
  - `PlanItemCard`
  - `VoteButtons`
  - `FriendRequestCard`
- Existing navigation/profile/dashboard pages now link into the collaborative planning flow.

## What Was Built
- Friends graph with search, request, accept/decline, list, and remove flow.
- Collaborative plans with host/member roles.
- Candidate plan items backed by the existing `places` table, so search and Google-backed place caching continue to work.
- Yes/no/maybe voting with one vote per user per candidate item.
- Automatic leading option calculation:
  1. more yes votes
  2. fewer no votes
  3. more maybe votes
- Host-controlled finalization with a final choice banner in the UI.
- Private saved lists preserved as lightweight personal organization.

## Validation
- Backend tests added for:
  - friend request + accept flow
  - collaborative plan voting + finalization
- Frontend validation run:
  - `npm run lint`
  - `npm run build`
- Backend validation run:
  - `pytest tests`
- Manual demo flow covered:
  - create two users
  - become friends
  - create plan
  - add candidate place
  - both users vote
  - finalize winning option

## Future Work
- Notifications/activity feed for new invites and vote changes.
- Multi-stop finalized plans.
- Share links and RSVP-style availability.
- Comments/chat inside a plan.
- Plan-level comments or lightweight chat.
- Calendar/date availability for group coordination.
