-- The Digest IR schema. Forward-only; the runner owns the transaction, so this
-- script carries NO explicit BEGIN/COMMIT/ROLLBACK. Keep schema.sql (the
-- declarative anchor) equal to the cumulative result of every migration.
--
-- `digests` stores a digest's metadata as typed columns and its segments
-- timeline as one JSON blob; `preferences` is per-user reading config; `history`
-- is scaffolded for a later resume/settings-used feature (no v1 code path).

CREATE TABLE digests (
    id                TEXT PRIMARY KEY,
    slug              TEXT NOT NULL UNIQUE,
    name              TEXT NOT NULL,
    prov_source_kind  TEXT NOT NULL,
    prov_origin       TEXT,
    prov_producer     TEXT,
    prov_ingested_via TEXT NOT NULL,
    prov_enriched     INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL,
    token_count       INTEGER NOT NULL,
    est_reading_ms    INTEGER NOT NULL,
    content_sha       TEXT NOT NULL,
    ir_version        INTEGER NOT NULL DEFAULT 1,
    owner_id          TEXT NOT NULL DEFAULT 'local',
    tags              TEXT NOT NULL DEFAULT '[]',
    reading_hint      TEXT,
    segments          TEXT NOT NULL
);

CREATE INDEX digests_created_at ON digests(created_at);

CREATE TABLE preferences (
    owner_id TEXT PRIMARY KEY,
    prefs    TEXT NOT NULL
);

CREATE TABLE history (
    id               TEXT PRIMARY KEY,
    digest_id        TEXT NOT NULL REFERENCES digests(id),
    owner_id         TEXT NOT NULL DEFAULT 'local',
    started_at       TEXT NOT NULL,
    segment_index    INTEGER NOT NULL DEFAULT 0,
    token_offset     INTEGER NOT NULL DEFAULT 0,
    completed_at     TEXT,
    settings_snapshot TEXT
);

-- The Digest IR supersedes the template example: drop the now-unused records
-- table (greenfield, no data). schema.sql carries no records table to match.
DROP TABLE records;
