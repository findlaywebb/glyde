-- Declarative schema anchor: the cumulative result of applying every migration
-- under migrations/, in order. This file is NEVER executed by the runner; a test
-- builds a database both ways (apply migrations vs run this script) and asserts
-- the two schemas converge. Keep it in lockstep with every new migration.

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
