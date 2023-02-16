import os
import pathlib
from dataclasses import dataclass
from sqlite3 import Connection

import anosql


@dataclass
class Migration:
    module: str
    filename: str

    @property
    def label(self):
        return os.path.join(
            self.module, "migrations", self.filename,
        )

    @property
    def path(self):
        root = pathlib.Path(__file__).parent.resolve()
        return os.path.join(root, self.label)


class Migrator:
    @staticmethod
    def init_migrations(db: Connection):
        cursor = db.cursor()
        cursor.execute(
            "create table if not exists "
            "migrations(filename text unique not null)")

    @staticmethod
    def _migration_is_applied(db: Connection, migration: Migration) -> bool:
        cursor = db.cursor()
        cursor.execute(
            "select count(1) from migrations "
            "where filename = ?",
            (migration.label,)
        )
        result = cursor.fetchall()[0][0]
        return bool(result)

    def apply_migrations(self, db: Connection, migrations: list):
        for migration in migrations:
            if self._migration_is_applied(db, migration):
                continue

            queries = anosql.from_path(migration.path, "sqlite3")

            for query in queries.available_queries:
                migrate = getattr(queries, query)
                migrate(db)
                db.commit()

            cursor = db.cursor()
            cursor.execute(
                "insert into migrations values (?)",
                (migration.label,)
            )
            db.commit()
