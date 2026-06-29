"""The declarative ``schema.sql`` anchor equals the migration result.

A database built by applying every migration must have the same schema as one
built by running the declarative ``schema.sql`` directly. This keeps the anchor
honest: it documents the cumulative schema, and the test fails the moment a new
migration lands without the anchor being updated to match.
"""

from contextlib import closing
from importlib.resources import files

from glyde.adapters.sqlite import apply_migrations, connect


def _schema_of(conn) -> list[str]:
    """Return the sorted CREATE statements of every table/index in the connection."""
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name"
    ).fetchall()
    return sorted(row["sql"].strip() for row in rows)


def test_migrations_converge_with_schema_sql(tmp_path) -> None:
    """Applying the migrations yields the same schema as running schema.sql."""
    migrated = tmp_path / "migrated.db"
    apply_migrations(migrated, backup_stamp="00000000T000000Z")

    declared = tmp_path / "declared.db"
    schema_sql = (files("glyde.adapters.sqlite") / "schema.sql").read_text()
    # closing(), not a bare `with connect()`: a sqlite3.Connection context manager does not
    # close on exit, and the leaked connection trips the ResourceWarning gate.
    with closing(connect(declared)) as conn:
        conn.executescript(schema_sql)

    with closing(connect(migrated)) as a, closing(connect(declared)) as b:
        assert _schema_of(a) == _schema_of(b)
