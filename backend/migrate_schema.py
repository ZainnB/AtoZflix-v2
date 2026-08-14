"""
Add any model columns that are missing from the live database.

WHY THIS EXISTS
---------------
`db.create_all()` only ever CREATEs tables. It will not ALTER a table that
already exists, so adding a column to a model leaves every existing database
silently missing it - the app then fails at query time with "no such column",
which is a confusing way to find out.

This walks the SQLAlchemy metadata, compares it against what the database
actually has, and issues `ALTER TABLE ... ADD COLUMN` for the difference. It is
idempotent: running it twice is a no-op.

SCOPE - read before relying on it
---------------------------------
This handles ADDED columns only. It deliberately does not attempt renames, type
changes, drops, or anything requiring data migration, because those cannot be
inferred from a schema diff and SQLite cannot express most of them without a
table rebuild.

Flask-Migrate/Alembic is already in requirements.txt and is the right tool for a
production migration history. This script exists because this project has no
migration history to build on, and inventing one retroactively for a portfolio
database is more ceremony than the problem deserves. If the schema starts
changing regularly, switch to `flask db migrate`.

Usage:
    python migrate_schema.py            # show and apply
    python migrate_schema.py --dry-run  # show only
"""

import argparse

from sqlalchemy import inspect, text

from app import create_app, db
from app.models import models  # noqa: F401  (registers the models on db.metadata)


def sql_type_for(column, dialect):
    """Render a column's type for this dialect, with a safe fallback."""
    try:
        return column.type.compile(dialect=dialect)
    except Exception:
        return "TEXT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("Schema reconciliation")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("=" * 70)

        # Create anything entirely absent first, so only real tables are diffed.
        db.create_all()

        inspector = inspect(db.engine)
        dialect = db.engine.dialect
        existing_tables = set(inspector.get_table_names())

        planned = []
        for table in db.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            live_columns = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in live_columns:
                    continue

                column_type = sql_type_for(column, dialect)
                clause = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}'

                # SQLite refuses ADD COLUMN ... NOT NULL without a default,
                # because existing rows would have nowhere to get a value.
                if not column.nullable:
                    if column.default is not None and column.default.arg is not None:
                        value = column.default.arg
                        literal = f"'{value}'" if isinstance(value, str) else (
                            "1" if value is True else "0" if value is False else str(value)
                        )
                        clause += f" NOT NULL DEFAULT {literal}"
                    else:
                        # Add it nullable rather than fail; a backfill can tighten it.
                        print(f"  ! {table.name}.{column.name} is NOT NULL with no "
                              f"default - adding as nullable")
                planned.append((table.name, column.name, column_type, clause))

        if not planned:
            print("\nNothing to do - database matches the models.")
            return

        print(f"\n{len(planned)} column(s) missing:\n")
        for table_name, column_name, column_type, _ in planned:
            print(f"  {table_name}.{column_name}  ({column_type})")

        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return

        print()
        for table_name, column_name, _, clause in planned:
            db.session.execute(text(clause))
            print(f"  added {table_name}.{column_name}")
        db.session.commit()

        print("\nDone.")


if __name__ == "__main__":
    main()
