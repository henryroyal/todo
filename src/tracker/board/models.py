from datetime import datetime
from pytz import utc
import os
import pathlib
from dataclasses import dataclass
from typing import List, Optional

import anosql
from flask import current_app

from src.tracker.auth.models import User
from src.tracker.task.models import Task, TaskSummary

sql_path = os.path.join(
    pathlib.Path(__file__).parent.resolve(), "queries.sql"
)

queries = anosql.from_path(sql_path, "sqlite3")


@dataclass
class UserRole:
    id: int
    board_id: int
    user_id: int
    role_name: str

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            board_id=row[1],
            user_id=row[2],
            role_name=row[3],
        )

    @staticmethod
    def accept_user_role(board_id: int, user_id: User):
        with current_app.database as db:
            queries.accept_board_user_role(
                db,
                board_id=board_id,
                user_id=user_id,
            )

    @classmethod
    def set_user_role(cls, user: User, board_id: int, user_id: int, role_name: str) -> 'UserRole':
        """
        Give grantee a specified role on the board
        If the user already has a defined role, update the value.
        """
        # todo - check user role
        with current_app.database as db:
            queries.set_board_user_role(
                db,
                board_id=board_id,
                user_id=user_id,
                role_name=role_name,
                invitation_from=user.id,
            )
            db.commit()

        return cls.get_user_role(board_id=board_id, user_id=user_id)

    @classmethod
    def get_user_role(cls, board_id: int, user_id: int) -> Optional['UserRole']:
        with current_app.database as db:
            response = queries.select_board_user(
                db, board_id, user_id
            )

        if not response:
            return

        user_role = response.pop(0)
        return cls._from_tuple(user_role)

    @classmethod
    def get_board_users(cls, board_id: int) -> List['UserRole']:
        with current_app.database as db:
            response = queries.select_board_user(db, board_id)

        return [
            cls._from_tuple(row) for row in response
        ]


@dataclass
class NewShareRequest:
    board_creator: str
    board_symbol: str
    board_name: str
    role_name: str

    @classmethod
    def _from_tuple(cls, row: tuple) -> 'NewShareRequest':
        return cls(
            board_creator=row[0],
            board_symbol=row[1],
            board_name=row[2],
            role_name=row[3],
        )

    @classmethod
    def list_user_share_requests_received(cls, user_id: int):
        with current_app.database as db:
            result = queries.list_user_share_requests_received(db, user_id=user_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]


@dataclass
class BoardUserRoleSummary:
    board_creator: str
    board_symbol: str
    username: str
    role: str
    is_active: bool
    is_invited: bool
    is_accepted: bool
    is_declined: bool

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            board_creator=row[0],
            board_symbol=row[1],
            username=row[2],
            role=row[3],
            is_active=row[4],
            is_invited=row[5],
            is_accepted=row[6],
            is_declined=row[7],
        )

    @classmethod
    def board_user_role_summary(cls, board_id: int, user_id: int) -> List['BoardUserRoleSummary']:
        with current_app.database as db:
            result = queries.board_user_role_summary(
                db,
                board_id=board_id,
                user_id=user_id,
            )

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def user_board_roles_summary(cls, user_id: int) -> List['BoardUserRoleSummary']:
        with current_app.database as db:
            result = queries.user_board_roles_summary(db, user_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]


@dataclass
class BoardStatus:
    id: int
    board_id: int
    name: str

    @classmethod
    def _from_tuple(cls, row: tuple) -> 'BoardStatus':
        return cls(
            id=row[0],
            board_id=row[1],
            name=row[2],
        )

    @classmethod
    def select_by_id(cls, status_id: int) -> Optional['BoardStatus']:
        with current_app.database as db:
            result = queries.select_board_status_by_id(
                db, status_id=status_id,
            )

        if not result:
            return

        status = result.pop(0)
        return cls._from_tuple(status)

    @classmethod
    def select_by_board_id(cls, board_id: int) -> List['BoardStatus']:
        """
        returns list of board statuses filtered by board_id
        """
        with current_app.database as db:
            result = queries.select_board_statuses(db, board_id)

        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def set_board_status(cls, board: 'Board', status: str) -> 'BoardStatus':
        """
        creates a default set of statuses for new board
        this is meant to leave the door open to
        extending with custom board statuses
        """
        with current_app.database as db:
            queries.set_board_status(db, board.id, status)
            db.commit()

    @classmethod
    def get_board_status(cls, board: 'Board', status: str):
        with current_app.database as db:
            result = queries.get_board_status(db, board.id, status)

        if not result:
            return

        status = result.pop(0)
        return cls._from_tuple(status)


@dataclass
class BoardSummary:
    id: int
    symbol: str
    name: str
    status: str
    creator_id: int
    creator: str
    role: str
    last_updated: int
    task_count: int
    user_count: int

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            symbol=row[1],
            name=row[2],
            status=row[3],
            creator_id=row[4],
            creator=row[5],
            role=row[6],
            last_updated=row[7],
            task_count=row[8],
            user_count=row[9],
        )


@dataclass
class Board:
    id: int
    symbol: str
    name: str

    creator: User
    created: int
    modified: Optional[int]

    current_status: BoardStatus
    possible_statuses: List[BoardStatus]

    task_seq: int
    tasks: List[Task]

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            creator=User.select_by_id(row[1]),
            symbol=row[2],
            task_seq=row[3],
            name=row[5],
            created=row[6],
            modified=row[7],

            tasks=Task.select_by_board_id(board_id=row[0]),
            current_status=BoardStatus.select_by_id(row[4]),
            possible_statuses=[
                s for s in BoardStatus.select_by_board_id(row[0]) if s.id != row[4]
            ]
        )

    @classmethod
    def select_by_id(cls, board_id: int) -> Optional['Board']:
        """
        Select by primary key
        """
        with current_app.database as db:
            result = queries.select_board_by_id(
                db, board_id
            )

        if not result:
            return None

        board = result.pop(0)
        return cls._from_tuple(board)

    @classmethod
    def select_by_creator_symbol(cls, creator_id: int, symbol: str) -> Optional['Board']:
        with current_app.database as db:
            result = queries.select_board_by_creator_symbol(
                db, creator_id, symbol
            )

        if not result:
            return

        board = result.pop(0)
        return cls._from_tuple(board)

    @classmethod
    def new_board(cls, symbol: str, name: str, creator: User) -> 'Board':
        """
        Construct new Board, persist it to database
        and return newly created entry.
        """
        with current_app.database as db:
            queries.create_new_board(
                db, symbol, name, creator.id, int(datetime.now(tz=utc).timestamp()),
            )
            db.commit()

        board = cls.select_by_creator_symbol(creator.id, symbol)
        board.set_user_role(creator, creator, "manager")
        board.accept_user_role(creator.id)
        with current_app.database as db:
            queries.add_board_status(db, creator_id=creator.id, symbol=symbol, status="todo")
            queries.add_board_status(db, creator_id=creator.id, symbol=symbol, status="in-progress")
            queries.add_board_status(db, creator_id=creator.id, symbol=symbol, status="completed")
            queries.set_board_status(db, board.id, "todo")
            db.commit()

        return cls.select_by_id(board.id)

    def delete(self):
        with current_app.database as db:
            queries.delete_board(db, self.id)
            queries.delete_board_tasks(db, self.id)
            queries.delete_board_statuses(db, self.id)
            queries.delete_board_roles(db, self.id)
            db.commit()

    def new_task(self, creator: User, title: str, body: str, assignee: User = None) -> Task:
        """
        Construct a Task, persist in database, return value
        """
        return Task.new_task(
            user=creator,
            board_id=self.id,
            creator_id=creator.id,
            title=title,
            body=body,
            assignee_id=assignee.id if assignee else None
        )

    def get_task(self, number: int) -> Optional[Task]:
        return Task.select_by_board_and_number(self.id, number)

    @staticmethod
    def board_tasks(user: User, board_id) -> List['TaskSummary']:
        with current_app.database as db:
            result = queries.board_tasks_summary(
                db,
                user_id=user.id,
                board_id=board_id
            )

        if not result:
            return list()

        return [
            TaskSummary._from_tuple(row) for row in result
        ]

    @staticmethod
    def user_boards(user: User) -> List[BoardSummary]:
        """
        Returns a list of boards belonging to user
        """
        # todo check user role
        with current_app.database as db:
            result = queries.user_boards_summary(db, user_id=user.id)

        if not result:
            return list()

        return [
            BoardSummary._from_tuple(row) for row in result
        ]

    def board_users(self) -> List[str]:
        with current_app.database as db:
            result = queries.list_user_share_for_assignees(db, self.id)

        if not result:
            return list()

        return [row[0] for row in result]

    @staticmethod
    def list_user_share_requests_received(user: User) -> List[NewShareRequest]:
        return NewShareRequest.list_user_share_requests_received(user.id)

    def board_users_summary(self, user: User) -> List[BoardUserRoleSummary]:
        return BoardUserRoleSummary.board_user_role_summary(
            board_id=self.id, user_id=user.id
        )

    def get_user_role(self, user: User, query_user: User) -> Optional[UserRole]:
        """

        """
        # todo - check user role before returning query_user role
        return UserRole.get_user_role(self.id, query_user.id)

    def set_user_role(self, user: User, grantee: User, role_name: str):
        """
        Give grantee a specified role on the board
        If the user already has a defined role, update the value.
        """
        # todo - check user role
        return UserRole.set_user_role(user, self.id, grantee.id, role_name)

    def accept_user_role(self, user_id: int):
        with current_app.database as db:
            queries.accept_board_user_role(
                db,
                board_id=self.id,
                user_id=user_id,
            )

    def decline_user_role(self, user_id: int):
        with current_app.database as db:
            queries.decline_board_user_role(
                db,
                board_id=self.id,
                user_id=user_id,
            )

    def delete_user_role(self, user: User, deleted: User):
        """
        Remove user from the board
        """
        # todo - check user role
        with current_app.database as db:
            queries.delete_board_user(
                db, self.id, deleted.id
            )
            db.commit()

    def user_can_view(self, user: User) -> bool:
        with current_app.database as db:
            result = queries.board_user_can_view(
                db,
                board_id=self.id,
                user_id=user.id,
            )

        if not result:
            return False

        return bool(result.pop(0)[0])

    def user_can_create(self, user: User) -> bool:
        with current_app.database as db:
            result = queries.board_user_can_create(
                db,
                board_id=self.id,
                user_id=user.id,
            )

        if not result:
            return False

        return bool(result.pop(0)[0])

    def user_can_edit(self, user: User) -> bool:
        with current_app.database as db:
            result = queries.board_user_can_edit(
                db,
                board_id=self.id,
                user_id=user.id,
            )

        if not result:
            return False

        return bool(result.pop(0)[0])

    def user_can_delete(self, user: User) -> bool:
        with current_app.database as db:
            result = queries.board_user_can_delete(
                db,
                board_id=self.id,
                user_id=user.id,
            )

        if not result:
            return False

        return bool(result.pop(0)[0])

    def user_can_invite(self, user: User) -> bool:
        with current_app.database as db:
            result = queries.board_user_can_invite(
                db,
                board_id=self.id,
                user_id=user.id,
            )

        if not result:
            return False

        return bool(result.pop(0)[0])

    def set_board_status(self, user: User, status: str) -> 'Board':
        """
        Update the board status
        """
        # todo - check user role
        with current_app.database as db:
            queries.set_board_status(
                db,
                board_id=self.id,
                name=status,

            )
            db.commit()
        return self.select_by_id(self.id)

    def rename_board(self, user: User, new_name: str) -> 'Board':
        """
        Update board name
        """
        # todo - check user role
        with current_app.database as db:
            queries.rename_board(
                db, new_name, self.id
            )
            db.commit()
        return self.select_by_id(self.id)

    def set_board_symbol(self, user: User, symbol: str) -> 'Board':
        """
        Update board symbol on board + tasks
        """
        # todo - check user role
        with current_app.database as db:
            queries.set_board_symbol(
                db, symbol=symbol, board_id=self.id
            )
            db.commit()
        return self.select_by_id(self.id)
