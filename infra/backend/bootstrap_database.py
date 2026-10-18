"""Initialize this application's fresh PostgreSQL identities from a protected file."""

import argparse
import json
from pathlib import Path

import psycopg
from psycopg import sql


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings", type=Path)
    parser.add_argument("--grant-runtime", action="store_true")
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text())
    with (
        psycopg.connect(settings["admin_url"], autocommit=True) as connection,
        connection.cursor() as cursor,
    ):
        if not args.grant_runtime:
            for role, password in [
                (settings["migration_role"], settings["migration_password"]),
                (settings["runtime_role"], settings["runtime_password"]),
            ]:
                cursor.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}"
                    ).format(sql.Identifier(role), sql.Literal(password))
                )
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(settings["database"]),
                    sql.Identifier(settings["migration_role"]),
                )
            )
    with (
        psycopg.connect(settings["migration_url"]) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        if args.grant_runtime:
            role = sql.Identifier(settings["runtime_role"])
            cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
            cursor.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
                ).format(role)
            )
            cursor.execute(
                sql.SQL(
                    "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}"
                ).format(role)
            )
            cursor.execute(
                sql.SQL(
                    "REVOKE INSERT, UPDATE, DELETE ON alembic_version FROM {}"
                ).format(role)
            )
    print("Project database identity step verified")


if __name__ == "__main__":
    main()
