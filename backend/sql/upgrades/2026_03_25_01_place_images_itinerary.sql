DO $$
BEGIN
  CREATE TYPE plan_step_type AS ENUM ('food', 'activity', 'dessert', 'drinks', 'custom');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE places
  ADD COLUMN IF NOT EXISTS image_url TEXT,
  ADD COLUMN IF NOT EXISTS google_photo_reference TEXT,
  ADD COLUMN IF NOT EXISTS photo_source TEXT,
  ADD COLUMN IF NOT EXISTS image_last_synced_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS external_photo_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_places_image_last_synced_at
  ON places(image_last_synced_at);

ALTER TABLE plan_items
  ADD COLUMN IF NOT EXISTS step_type plan_step_type NOT NULL DEFAULT 'custom',
  ADD COLUMN IF NOT EXISTS order_index INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_selected BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

UPDATE plan_items
SET order_index = ordered.position
FROM (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY plan_id ORDER BY created_at, id) - 1 AS position
  FROM plan_items
) AS ordered
WHERE plan_items.id = ordered.id
  AND plan_items.order_index = 0;

CREATE INDEX IF NOT EXISTS idx_plan_items_plan_order
  ON plan_items(plan_id, order_index);
