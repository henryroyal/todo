from datetime import datetime
from pytz import utc
import os
import pathlib
import time
from dataclasses import dataclass, field
from hashlib import scrypt
from typing import List, Tuple
from typing import Optional

import anosql
from flask import current_app
from flask.sessions import SessionMixin

sql_path = os.path.join(
    pathlib.Path(__file__).parent.resolve(), "queries.sql"
)

queries = anosql.from_path(sql_path, "sqlite3")


@dataclass
class Role:
    id: int
    name: str

    @classmethod
    def _build_from_tuple(cls, row: tuple):
        role = cls(
            id=row[0],
            name=row[1],
        )
        return role

    @classmethod
    def select_by_name(cls, role_name: str) -> Optional['Role']:
        with current_app.database as db:
            response = queries.select_role_by_name(
                db, role_name=role_name,
            )

        if not response:
            return

        role = response.pop(0)
        return cls._build_from_tuple(role)

    @classmethod
    def select_by_id(cls, role_id: int) -> Optional['Role']:
        with current_app.database as db:
            response = queries.select_role_by_id(
                db, role_id
            )

        if not response:
            return

        role = response.pop(0)
        return cls._build_from_tuple(role)


@dataclass
class User:
    id: Optional[int]
    username: str
    password: bytes
    is_admin: bool
    is_active: bool
    created: int
    modified: Optional[int]

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            username=row[1],
            password=row[2],
            is_admin=bool(row[3]),
            is_active=bool(row[4]),
            created=row[5],
            modified=row[6],
        )

    @classmethod
    def _new_user(
            cls,
            username: str,
            password: bytes,
            is_admin: bool,
            is_active: bool,
    ) -> 'User':
        hashed_password = cls.hash_password(password)
        user = cls(
            id=None,
            username=str(username),
            password=hashed_password,
            is_admin=bool(is_admin),
            is_active=bool(is_active),
            created=int(datetime.now(tz=utc).timestamp()),
            modified=None,
        )
        return user

    @classmethod
    def create_user(
            cls,
            username: str,
            password: bytes,
    ) -> 'User':
        user = cls._new_user(username, password, False, True)
        with current_app.database as db:
            queries.create_user(
                db,
                username=user.username,
                password=user.password,
                created=user.created,
                is_admin=user.is_admin,
                is_active=user.is_active,
            )
            db.commit()

        return cls.select_by_username(username)

    @classmethod
    def create_admin(
            cls,
            username: str,
            password: bytes,
    ) -> 'User':
        user = cls._new_user(username, password, True, True)
        with current_app.database as db:
            queries.create_user(
                db,
                username=user.username,
                password=user.password,
                created=user.created,
                is_admin=user.is_admin,
                is_active=user.is_active,
            )
            db.commit()

        return cls.select_by_username(username)

    @classmethod
    def select_by_id(cls, user_id: int) -> Optional['User']:
        with current_app.database as db:
            response = queries.select_user_by_id(
                db, user_id=user_id
            )

        if not response:
            return

        user = cls._from_tuple(response.pop(0))
        return user

    @classmethod
    def select_by_username(cls, username: str) -> Optional['User']:
        with current_app.database as db:
            response = queries.select_user_by_username(
                db, username
            )

        if not response:
            return

        if len(response) != 1:
            raise ValueError("Expected single user")

        user = response.pop(0)
        return cls._from_tuple(user)

    @classmethod
    def all_users_for_admin(cls) -> List:
        with current_app.database as db:
            response = queries.select_all_users_for_admin(db)
        if not response:
            return list()
        return response

    @staticmethod
    def hash_password(password: bytes) -> bytes:
        """https://datatracker.ietf.org/doc/html/rfc7914.html#section-2"""
        salt = bytes(current_app.config["PASSWORD_SALT"], "utf8")
        return scrypt(password, salt=salt, n=16384, r=1, p=1)

    def verify_password(self, guessed_password) -> bool:
        return self.password == self.hash_password(guessed_password)

    @classmethod
    def from_flask_session(cls, s: SessionMixin) -> Optional['User']:
        if "username" not in s or not s["username"]:
            return None

        user = cls.select_by_username(s["username"])
        if user is None:
            del s["username"]
            return None

        if not user.is_active:
            return None

        return user
