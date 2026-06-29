-- Initial schema. Forward-only; the runner owns the transaction, so this script
-- carries NO explicit BEGIN/COMMIT/ROLLBACK. Keep schema.sql (the declarative
-- anchor) equal to the cumulative result of every migration.

CREATE TABLE records (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
