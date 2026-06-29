-- Declarative schema anchor: the cumulative result of applying every migration
-- under migrations/, in order. This file is NEVER executed by the runner; a test
-- builds a database both ways (apply migrations vs run this script) and asserts
-- the two schemas converge. Keep it in lockstep with every new migration.

CREATE TABLE records (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
