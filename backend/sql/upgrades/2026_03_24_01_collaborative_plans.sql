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
