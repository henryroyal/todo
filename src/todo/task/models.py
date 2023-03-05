from datetime import datetime
from pytz import utc
import os
import pathlib
import time
from dataclasses import dataclass, field
from typing import List, Optional

import anosql
from flask import current_app

from src.todo.auth.models import User

sql_path = os.path.join(
    pathlib.Path(__file__).parent.resolve(), "queries.sql"
)

queries = anosql.from_path(sql_path, "sqlite3")


def task_search(user: User, query: str) -> List[tuple]:
    if not query:
        return list()

    with current_app.database as db:
        results = queries.query_task_search(db, query)
        allowed = set(
            i[0] for i in queries.filter_search_result_by_user(db, user.id)
        )

    if not results or not allowed:
        return list()

    return [
        r for r in results if r[0] in allowed
    ]


@dataclass
class TaskEvent:
    id: int
    task_id: int
    user_id: int
    created: int
    description: str
    change_field: Optional[str] = None
    change_old: Optional[str] = None
    change_new: Optional[str] = None

    @classmethod
    def _from_tuple(cls, row: tuple) -> 'TaskEvent':
        return cls(
            id=row[0],
            task_id=row[1],
            user_id=row[2],
            created=row[3],
            description=row[4],
            change_field=row[5],
            change_old=row[6],
            change_new=row[7],
        )

    @classmethod
    def select_by_task_id(cls, task_id: int) -> List['TaskEvent']:
        with current_app.database as db:
            result = queries.select_task_events_by_task_id(db, task_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def new_task_event(
            cls,
            task_id: int,
            user_id: int,
            description: str,
            change_field: str = None,
            change_old: str = None,
            change_new: str = None,
    ) -> 'TaskEvent':
        """
        Create new task event history item
        """
        with current_app.database as db:
            queries.create_task_event(
                db,
                task_id,
                user_id,
                int(datetime.now(tz=utc).timestamp()),
                description,
                change_field,
                change_old,
                change_new,
            )
            db.commit()


@dataclass
class TaskTag:
    id: int
    task_id: int
    value: str

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            task_id=row[1],
            value=row[2],
        )

    @classmethod
    def set_task_tag(cls, task_id, value: str) -> 'TaskTag':
        with current_app.database as db:
            queries.set_task_tag(db, task_id, value)
            db.commit()
        return cls.select_task_tag(task_id, value)

    @classmethod
    def select_task_tag(cls, task_id: int, value: str) -> Optional['TaskTag']:
        with current_app.database as db:
            result = queries.select_task_tag(db, task_id, value)
        if not result:
            return
        tag = result.pop(0)
        return cls._from_tuple(tag)

    @classmethod
    def select_task_tags(cls, task_id: int) -> List['TaskTag']:
        with current_app.database as db:
            result = queries.select_task_tags(db, task_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]

    @staticmethod
    def delete_task_tags(task_id: int):
        with current_app.database as db:
            queries.delete_task_tags(db, task_id)
            db.commit()

    @staticmethod
    def delete_task_tag(tag_id: int):
        with current_app.database as db:
            queries.delete_task_tag(db, tag_id)
            db.commit()


@dataclass
class TaskComment:
    id: int
    task_id: int
    number: int
    user: User
    contents: str
    created: int
    modified: Optional[int]

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            task_id=row[1],
            number=row[2],
            user=User.select_by_id(row[3]),
            contents=row[4],
            created=row[5],
            modified=row[6],
        )

    @classmethod
    def select_by_task_id(cls, task_id: int) -> List['TaskComment']:
        with current_app.database as db:
            result = queries.select_task_comments_by_task_id(db, task_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def select_by_task_id_and_comment_number(
            cls,
            task_id: int,
            comment_number: int,
    ) -> Optional['TaskComment']:
        with current_app.database as db:
            result = queries. \
                select_task_comment_by_task_id_and_comment_number(
                db, task_id, comment_number)

        if not result:
            return

        comment = result.pop(0)
        return cls._from_tuple(comment)

    @classmethod
    def new_task_comment(
            cls,
            task_id: int,
            user_id: int,
            contents: str,
    ) -> 'TaskComment':
        """
        Create new task comment item
        """
        with current_app.database as db:
            queries.increment_comment_number_sequence(db, task_id)
            number = queries.select_comment_number_sequence(db, task_id)[0][0]
            queries.create_task_comment(
                db, task_id, number, user_id, contents, int(datetime.now(tz=utc).timestamp())
            )
            db.commit()

        return cls.select_by_task_id_and_comment_number(task_id, number)

    @classmethod
    def edit_task_comment(cls, task_id: int, task_number: int, contents: str) -> 'TaskComment':
        """
        Modify comment contents
        """
        # todo - check user
        with current_app.database as db:
            modified = int(time.time())
            queries.edit_task_comment(
                db,
                contents=contents,
                modified=modified,
                task_id=task_id,
                number=task_number,
            )
            db.commit()

        comment = cls.select_by_task_id_and_comment_number(task_id, task_number)
        return comment

    @staticmethod
    def delete_task_comment(task_id: int, number: int):
        with current_app.database as db:
            queries.delete_task_comment(db, task_id, number)

    @staticmethod
    def select_board_task_summary(board_id: int) -> List['TaskSummary']:
        with current_app as db:
            results = queries.board_task_summary(db, board_id)


@dataclass
class TaskStatus:
    id: Optional[int]
    task_id: int
    name: str

    @classmethod
    def _from_tuple(cls, row: tuple) -> 'TaskStatus':
        return cls(
            id=row[0],
            task_id=row[1],
            name=row[2],
        )

    @classmethod
    def select_by_id(cls, status_id: int) -> Optional['TaskStatus']:
        with current_app.database as db:
            result = queries.select_task_status_by_id(db, status_id)
        if not result:
            return
        status = result.pop(0)
        return cls._from_tuple(status)

    @classmethod
    def select_by_task_id(cls, task_id: int) -> List['TaskStatus']:
        with current_app.database as db:
            result = queries.select_task_statuses(db, task_id)
        if not result:
            return list()
        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def select_by_task_and_name(cls, task_id: int, name: str) -> Optional['TaskStatus']:
        with current_app.database as db:
            result = queries.select_task_status(db, task_id, name)
        if not result:
            return
        status = result.pop(0)
        return cls._from_tuple(status)

    @classmethod
    def create_task_status(cls, task_id: int, name: str) -> 'TaskStatus':
        with current_app.database as db:
            queries.create_task_status(
                db,
                task_id=task_id,
                name=name,
            )
            db.commit()
        return cls.select_by_task_and_name(task_id, name)

    @staticmethod
    def delete_task_statuses(task_id: int):
        with current_app.database as db:
            queries.delete_task_statuses(db, task_id)
            db.commit()


@dataclass
class TaskSummary:
    symbol: str
    number: int
    description: str
    status: str
    creator: str
    assignee: Optional[str]
    tag_count: int
    comment_count: int
    last_updated: int

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            symbol=row[0],
            number=row[1],
            description=row[2],
            status=row[3],
            creator=row[4],
            assignee=row[5] or "None",
            tag_count=row[6],
            comment_count=row[7],
            last_updated=row[8],
        )


@dataclass
class Task:
    id: Optional[int]
    number: int
    board_id: int
    creator_id: int
    assignee_id: Optional[int]
    title: str
    body: str
    created: int
    modified: Optional[int]

    status: Optional[TaskStatus] = None
    possible_statuses: List[TaskStatus] = field(default_factory=list)

    tags: List[TaskTag] = field(default_factory=list)
    comments: List[TaskComment] = field(default_factory=list)
    events: List[TaskEvent] = field(default_factory=list)

    @classmethod
    def _from_tuple(cls, row: tuple):
        return cls(
            id=row[0],
            number=row[1],
            board_id=row[2],
            creator_id=row[3],
            assignee_id=row[4],
            title=row[6],
            body=row[7],
            created=row[8],
            modified=row[9],
            tags=TaskTag.select_task_tags(row[0]),
            comments=TaskComment.select_by_task_id(row[0]),
            events=TaskEvent.select_by_task_id(row[0]),
            status=TaskStatus.select_by_id(row[5]),
            possible_statuses=[
                s for s in TaskStatus.select_by_task_id(row[0]) if s.id != row[5]
            ]
        )

    @classmethod
    def select_by_task_id(cls, task_id: int) -> Optional['Task']:
        with current_app.database as db:
            result = queries.select_task_by_task_id(db, task_id)

        if not result:
            return

        task = result.pop(0)
        return cls._from_tuple(task)

    @classmethod
    def select_by_board_id(cls, board_id: int) -> List['Task']:
        with current_app.database as db:
            result = queries.select_tasks_by_board_id(db, board_id)

        if not result:
            return list()

        return [
            cls._from_tuple(row) for row in result
        ]

    @classmethod
    def select_by_board_and_number(cls, board_id: int, task_number: int):
        """
        Select using the board_id and board task_seq
        """
        with current_app.database as db:
            result = queries.select_task_by_board_number(
                db, board_id, task_number
            )

        if not result:
            return None

        board = result.pop(0)
        return cls._from_tuple(board)

    @classmethod
    def user_tasks(cls, user: User) -> List[TaskSummary]:
        with current_app.database as db:
            result = queries.user_tasks_summary(db, user.id)
        if not result:
            return list()
        return [
            TaskSummary._from_tuple(row) for row in result
        ]

    @classmethod
    def new_task(
            cls,
            user: User,
            board_id: int,
            creator_id: int,
            title: str,
            body: str,
            assignee_id: int = None,
    ) -> 'Task':
        """
        Create and persist a new Task
        Return newly created object
        """
        with current_app.database as db:
            queries.increment_task_number_sequence(db, board_id)
            task_number = queries.select_task_number_sequence(db, board_id)[0][0]
            queries.create_new_task(
                db,
                task_number,
                board_id,
                creator_id,
                assignee_id,
                title,
                body,
                int(time.time()),
            )
            db.commit()

        task = Task.select_by_board_and_number(board_id, task_number)
        TaskEvent.new_task_event(task.id, user.id, description="created task")
        TaskStatus.create_task_status(task.id, "todo")
        TaskStatus.create_task_status(task.id, "in-progress")
        TaskStatus.create_task_status(task.id, "completed")
        task = task.set_status(user, "todo")
        return task

    def delete(self, user: User):
        with current_app.database as db:
            queries.delete_task(db, self.id)
            queries.delete_task_comments(db, self.id)
            queries.delete_task_statuses(db, self.id)
            queries.delete_task_tags(db, self.id)
            queries.delete_task_events(db, self.id)
            db.commit()

    def set_status(self, user: User, name: str) -> 'Task':
        status = TaskStatus.select_by_task_and_name(self.id, name)
        if not status:
            print("no status")
            return

        with current_app.database as db:
            queries.set_task_status(db, status_id=status.id, task_id=self.id)
            db.commit()

        task = self.select_by_task_id(self.id)
        TaskEvent.new_task_event(self.id, user.id, "update", "status", task.status.id)
        return task

    def get_statuses(self) -> List[TaskStatus]:
        return TaskStatus.select_by_task_id(self.id)

    def set_assignee(self, user: User, assignee: Optional[int]) -> 'Task':
        """
        Update task assignee, return updated task
        """
        old_assignee = User.select_by_id(self.assignee_id)
        if assignee:
            new_assignee = User.select_by_id(assignee)
            if not new_assignee:
                raise ValueError(f"cannot assign to {assignee}: user not found")
        else:
            new_assignee = None

        with current_app.database as db:
            modified = int(time.time())
            queries.set_task_assignee(
                db,
                new_assignee.id if new_assignee else None,
                modified,
                self.id,
            )
            db.commit()

        task = self.select_by_task_id(self.id)
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "update",
            "assignee",
            old_assignee.username if old_assignee else None,
            new_assignee.username if new_assignee else None,
        )
        return task

    def set_title(self, user: User, title: str) -> 'Task':
        """
        Update task title, return updated task
        """
        old_title = self.title
        with current_app.database as db:
            modified = int(time.time())
            queries.set_task_title(db, title, modified, self.id)
            db.commit()

        TaskEvent.new_task_event(
            self.id,
            user.id,
            "update",
            "title",
            old_title,
            title,
        )
        return self.select_by_task_id(self.id)

    def set_body(self, user: User, contents: str) -> 'Task':
        """
        Update main text body of task, return updated task
        """
        old_contents = self.body
        with current_app.database as db:
            modified = int(time.time())
            queries.set_task_body(db, contents, modified, self.id)
            db.commit()

        TaskEvent.new_task_event(
            self.id,
            user.id,
            "update",
            "body",
            old_contents,
            contents,
        )
        return self.select_by_task_id(self.id)

    def new_comment(self, user: User, contents: str) -> 'Task':
        """
        Create new comment associated with task
        """
        TaskComment.new_task_comment(self.id, user.id, contents)
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "new",
            "comment",
            "",
            contents,
        )
        return self.select_by_task_id(self.id)

    def edit_comment(self, user: User, comment_number: int, contents: str) -> 'Task':
        """
        Modify comment contents
        """
        old_comment = TaskComment.select_by_task_id_and_comment_number(self.id, comment_number)
        new_comment = old_comment.edit_task_comment(self.id, comment_number, contents)
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "edit",
            "comment",
            old_comment.contents,
            new_comment.contents,
        )
        return self.select_by_task_id(self.id)

    def delete_comment(self, user: User, comment_number: int) -> 'Task':
        """
        Delete comment
        """
        comment = TaskComment.select_by_task_id_and_comment_number(self.id, comment_number)
        if not comment:
            return self.select_by_task_id(self.id)

        comment.delete_task_comment(self.id, comment_number)
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "delete",
            "comment",
            str(comment.number)
        )
        return self.select_by_task_id(self.id)

    def add_tag(self, user: User, value: str) -> 'Task':
        tag = TaskTag.set_task_tag(self.id, value.lower())
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "new",
            "tag",
            None,
            tag.value,
        )
        return self.select_by_task_id(self.id)

    def remove_tag(self, user: User, value: str) -> 'Task':
        tag = TaskTag.select_task_tag(self.id, value.lower())
        if not tag:
            return self.select_by_task_id(self.id)

        TaskTag.delete_task_tag(tag.id)
        TaskEvent.new_task_event(
            self.id,
            user.id,
            "delete",
            "tag",
            tag.value,
            None,
        )
        return self.select_by_task_id(self.id)
