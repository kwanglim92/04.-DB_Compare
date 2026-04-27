-- Migration: Add checklist_mappings table to existing container
-- Apply with:
--   docker exec -i dbmanager-postgres psql -U dbmanager -d dbmanager < init/03_checklist_mappings.sql

CREATE TABLE IF NOT EXISTS checklist_mappings (
    id          SERIAL PRIMARY KEY,
    model       VARCHAR(200) NOT NULL,
    module      VARCHAR(200) NOT NULL,
    item_norm   VARCHAR(500) NOT NULL,
    db_key      VARCHAR(500) NOT NULL,
    confidence  NUMERIC(3,2) NOT NULL DEFAULT 0.95,
    verified_by VARCHAR(200),
    verified_at TIMESTAMPTZ DEFAULT NOW(),
    source      VARCHAR(50) NOT NULL DEFAULT 'manual',
    UNIQUE(model, module, item_norm)
);

CREATE INDEX IF NOT EXISTS idx_checklist_mappings_model ON checklist_mappings(model);

INSERT INTO sync_versions (table_name, version) VALUES ('checklist_mappings', 1)
    ON CONFLICT (table_name) DO NOTHING;
