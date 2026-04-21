-- DB_Manager Schema
-- Auto-executed on first container startup via docker-entrypoint-initdb.d

-- ===========================================
-- specs: Common Base spec items
-- ===========================================
CREATE TABLE specs (
    id          SERIAL PRIMARY KEY,
    module      VARCHAR(100) NOT NULL,      -- e.g. "Dsp"
    part_type   VARCHAR(100) NOT NULL,      -- e.g. "XScanner"
    part_name   VARCHAR(100) NOT NULL,      -- e.g. "100um"
    item_name   VARCHAR(200) NOT NULL,      -- e.g. "ServoCutoffFrequencyHz"
    validation_type VARCHAR(50) NOT NULL DEFAULT 'range',  -- "range" | "exact"
    min_spec    DOUBLE PRECISION,           -- for range validation
    max_spec    DOUBLE PRECISION,           -- for range validation
    expected_value VARCHAR(200),            -- for exact validation
    unit        VARCHAR(50) DEFAULT '',
    enabled     BOOLEAN DEFAULT TRUE,
    description VARCHAR(500) DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(module, part_type, part_name, item_name)
);

-- ===========================================
-- profiles: Equipment profile metadata
-- ===========================================
CREATE TABLE profiles (
    id              SERIAL PRIMARY KEY,
    profile_name    VARCHAR(200) NOT NULL UNIQUE,
    description     VARCHAR(500) DEFAULT '',
    inherits_from   VARCHAR(200) DEFAULT 'Common_Base',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ===========================================
-- profile_excluded_items: Items excluded per profile
-- ===========================================
CREATE TABLE profile_excluded_items (
    id          SERIAL PRIMARY KEY,
    profile_id  INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    pattern     VARCHAR(500) NOT NULL,      -- e.g. "Dsp.XScanner.5um.ServoCutoffFrequencyHz"
    UNIQUE(profile_id, pattern)
);

-- ===========================================
-- profile_overrides: Per-profile spec overrides
-- ===========================================
CREATE TABLE profile_overrides (
    id              SERIAL PRIMARY KEY,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    module          VARCHAR(100) NOT NULL,
    part_type       VARCHAR(100) NOT NULL,
    part_name       VARCHAR(100) NOT NULL,
    item_name       VARCHAR(200) NOT NULL,
    validation_type VARCHAR(50) NOT NULL DEFAULT 'range',
    min_spec        DOUBLE PRECISION,
    max_spec        DOUBLE PRECISION,
    expected_value  VARCHAR(200),
    unit            VARCHAR(50) DEFAULT '',
    enabled         BOOLEAN DEFAULT TRUE,
    description     VARCHAR(500) DEFAULT '',
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_id, module, part_type, part_name, item_name)
);

-- ===========================================
-- profile_additional_checks: Extra items per profile
-- ===========================================
CREATE TABLE profile_additional_checks (
    id              SERIAL PRIMARY KEY,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    module          VARCHAR(100) NOT NULL,
    part_type       VARCHAR(100) NOT NULL,
    part_name       VARCHAR(100) NOT NULL,
    item_name       VARCHAR(200) NOT NULL,
    validation_type VARCHAR(50) NOT NULL DEFAULT 'range',
    min_spec        DOUBLE PRECISION,
    max_spec        DOUBLE PRECISION,
    expected_value  VARCHAR(200),
    unit            VARCHAR(50) DEFAULT '',
    enabled         BOOLEAN DEFAULT TRUE,
    description     VARCHAR(500) DEFAULT '',
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_id, module, part_type, part_name, item_name)
);

-- ===========================================
-- sync_versions: Version tracking for sync
-- ===========================================
CREATE TABLE sync_versions (
    id          SERIAL PRIMARY KEY,
    table_name  VARCHAR(100) NOT NULL UNIQUE,  -- "specs", "profiles", etc.
    version     INTEGER NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Initialize version tracking
INSERT INTO sync_versions (table_name, version) VALUES
    ('specs', 1),
    ('profiles', 1);

-- ===========================================
-- Trigger: auto-update updated_at and bump version
-- ===========================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER specs_updated
    BEFORE UPDATE ON specs
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER profiles_updated
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER overrides_updated
    BEFORE UPDATE ON profile_overrides
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER additional_checks_updated
    BEFORE UPDATE ON profile_additional_checks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Version bump function (call after data changes)
CREATE OR REPLACE FUNCTION bump_version(target_table VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE sync_versions
    SET version = version + 1, updated_at = NOW()
    WHERE table_name = target_table;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Indexes
-- ===========================================
CREATE INDEX idx_specs_module ON specs(module);
CREATE INDEX idx_specs_lookup ON specs(module, part_type, part_name);
CREATE INDEX idx_overrides_profile ON profile_overrides(profile_id);
CREATE INDEX idx_additional_profile ON profile_additional_checks(profile_id);
CREATE INDEX idx_excluded_profile ON profile_excluded_items(profile_id);
