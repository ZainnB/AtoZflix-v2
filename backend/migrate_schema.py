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

from app.utils.helpers import safe_database_uri
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
        print(f"Database: {safe_database_uri(app.config['SQLALCHEMY_DATABASE_URI'])}")
        print("=" * 70)

        # Create anything entirely absent first, so only real tables are diffed.
        db.create_all()

        inspector = inspect(db.engine)
        dialect = db.engine.dialect
        # Identifiers have to be quoted the way THIS dialect quotes them.
        # Double quotes are the SQL standard and are what SQLite uses, but
        # MySQL reads "Movies" as a string literal unless ANSI_QUOTES is set,
        # so a hand-rolled f-string produced error 1064 there. The dialect's
        # own preparer emits backticks on MySQL and double quotes on SQLite,
        # and also quotes reserved words such as "rank" correctly.
        quote = dialect.identifier_preparer.quote
        # Compared case-insensitively, deliberately. MySQL on Windows runs
        # with lower_case_table_names=1 and folds every identifier to lower
        # case, so the inspector returns "actors" where the model declares
        # "Actors". An exact match skipped every table and then reported
        # "Nothing to do" while ten columns were in fact missing - a silent
        # no-op being a far worse failure here than an error would be.
        existing_tables = {t.lower() for t in inspector.get_table_names()}

        planned = []
        for table in db.metadata.sorted_tables:
            if table.name.lower() not in existing_tables:
                continue
            live_columns = {c["name"].lower()
                            for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name.lower() in live_columns:
                    continue

                column_type = sql_type_for(column, dialect)
                clause = (f"ALTER TABLE {quote(table.name)} "
                          f"ADD COLUMN {quote(column.name)} {column_type}")

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

        # Columns the DATABASE has that the models no longer declare.
        #
        # Not dropped - that needs a human decision and possibly a data
        # migration - but reported loudly, because a leftover NOT NULL column
        # with no default breaks every INSERT the application makes while
        # being completely invisible to the missing-column diff above. The
        # error MySQL raises names the column but not the reason, so this is
        # the report that turns a baffling 1364 into an obvious one-line fix.
        stale = []
        for table in db.metadata.sorted_tables:
            if table.name.lower() not in existing_tables:
                continue
            declared = {c.name.lower() for c in table.columns}
            for live in inspector.get_columns(table.name):
                if live["name"].lower() in declared:
                    continue
                blocking = (not live.get("nullable", True)
                            and live.get("default") is None)
                stale.append((table.name, live["name"], live.get("type"), blocking))

        if stale:
            print(f"\n{len(stale)} column(s) in the database are not in the models:\n")
            for table_name, column_name, column_type, blocking in stale:
                flag = ("  <-- NOT NULL, no default: BREAKS EVERY INSERT"
                        if blocking else "")
                print(f"  {table_name}.{column_name}  ({column_type}){flag}")
            if any(b for *_, b in stale):
                print()
                print("  Every INSERT into the table(s) flagged above fails with")
                print("  MySQL error 1364. Either drop the column:")
                for table_name, column_name, _t, blocking in stale:
                    if blocking:
                        print(f"    ALTER TABLE {quote(table_name)} "
                              f"DROP COLUMN {quote(column_name)};")
                print("  or make it nullable, if the data still matters.")

        if not planned:
            if not stale:
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
