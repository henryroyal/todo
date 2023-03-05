import time

import pytest

from src.todo.auth.models import User
from src.todo.board.models import Board
from src.todo.task.models import Task, TaskStatus, TaskTag, TaskComment, TaskEvent, task_search


@pytest.fixture()
def text_fixture_1():
    return ("Sonnet 1 by Sir Philip Sidney",
            """Loving in truth, and fain in verse my love to show,
That she, dear she, might take some pleasure of my pain,
Pleasure might cause her read, reading might make her know,
Knowledge might pity win, and pity grace obtain,—
I sought fit words to paint the blackest face of woe,
Studying inventions fine, her wits to entertain,
Oft turning others’ leaves, to see if thence would flow
Some fresh and fruitful showers upon my sunburned brain.
But words came halting forth, wanting Invention’s stay:
Invention, Nature’s child, fled step-dame Study’s blows,
And others’ feet still seemed but strangers in my way.
Thus great with child to speak, and helpless in my throes,
Biting my truant pen, beating myself for spite:
“Fool,” said my Muse to me, “look in thy heart and write.”""")


@pytest.fixture()
def text_fixture_2():
    return ("Sonnet by Francesco Petrarca (Translated by Thomas Wentworth Higginson)",
            """O ye who trace through scattered verse the sound
Of those long sighs wherewith I fed my heart
Amid youth’s errors, when in greater part
That man unlike this present man was found;
For the mixed strain which here I do compound
Of empty hopes and pains that vainly start,
Whatever soul hath truly felt love’s smart,
With pity and with pardon will abound.
But now I see full well how long I earned
All men’s reproof; and oftentimes my soul
Lies crushed by its own grief; and it doth seem
For such misdeed shame is the fruitage whole,
And wild repentance and the knowledge learned
That worldly joy is still a short, short dream.""")


@pytest.fixture
def user(app):
    with app.app_context():
        user = User.create_user("username", b'password')
    return user


@pytest.fixture
def board(app, user):
    with app.app_context():
        board = Board.new_board("TST", "Board", user)
    return board


@pytest.mark.freeze_time("2023-01-01")
def test_create_new_board_task(app, user, board):
    with app.app_context():
        board.new_task(
            creator=user,
            title="new task",
            body="steps\n1.) test",
            assignee=user,
        )

        task = Task.select_by_board_id(1)
        assert task

        task = Task.select_by_board_and_number(1, 1)
        assert task

        assert task.creator_id == user.id
        assert task.board_id == board.id
        assert task.title == "new task"
        assert task.body == "steps\n1.) test"
        assert task.assignee_id == user.id
        assert task.created == 1672531200
        assert task.modified is None


def test_set_task_status(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        statuses = task.get_statuses()
        names = [s.name for s in statuses]
        assert names == ["completed", "in-progress", "todo"]

        task = Task.select_by_board_and_number(board.id, task.number)
        todo = TaskStatus.select_by_task_and_name(task.id, "todo")
        assert task.status.id == todo.id

        task = task.set_status(user, "in-progress")
        progress = TaskStatus.select_by_task_and_name(task.id, "in-progress")
        assert task.status.id == progress.id

        task = task.set_status(user, "completed")
        completed = TaskStatus.select_by_task_and_name(task.id, "completed")
        assert task.status.id == completed.id


@pytest.mark.freeze_time("2023-01-01")
def test_create_task_comment(app, user, board):
    with app.app_context():
        board.new_task(
            creator=user,
            title="Task #1",
            body="",
        )
        task = board.new_task(
            creator=user,
            title="Task #2",
            body="",
        )

        task = task.new_comment(user, "hello world")
        assert len(task.comments) == 1

        comment = task.comments[0]
        assert comment.task_id == task.id
        assert comment.user.id == user.id
        assert comment.contents == "hello world"
        assert comment.created == 1672531200


def test_task_comments_sorted_by_create_timestamp(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.new_comment(user, "hello world")
        assert len(task.comments) == 1
        assert task.comments[0].contents == "hello world"
        assert task.comments[0].number == 1

        time.sleep(2)

        task = task.new_comment(user, "hello again")
        assert len(task.comments) == 2
        assert task.comments[0].contents == "hello again"
        assert task.comments[0].number == 2


def test_edit_task_comment(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )
        task = task.new_comment(user, "hello world")
        number = task.comments[0].number
        assert task.comments[0].modified is None

        task = task.edit_comment(user, number, "hello again")
        assert task.comments[0].contents == "hello again"
        modified = task.comments[0].modified

        time.sleep(2)

        task = task.edit_comment(user, number, "goodbye")
        assert task.comments[0].contents == "goodbye"
        assert task.comments[0].modified > modified


def test_delete_task_comment(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.new_comment(user, "hello world")
        task.delete_comment(user, task.comments[0].number)
        assert TaskComment.select_by_task_id(task.id) == list()


def test_delete_board_task(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.new_comment(user, "hello world")
        task = task.add_tag(user, "test")
        assert len(TaskComment.select_by_task_id(task.id)) == 1
        assert len(TaskStatus.select_by_task_id(task.id)) == 3
        assert len(TaskTag.select_task_tags(task.id)) == 1
        assert len(TaskEvent.select_by_task_id(task.id)) == 4

        task.delete(user)

        assert Task.select_by_task_id(task.id) is None
        assert TaskComment.select_by_task_id(task.id) == list()
        assert TaskStatus.select_by_task_id(task.id) == list()
        assert TaskTag.select_task_tags(task.id) == list()
        assert TaskEvent.select_by_task_id(task.id) == list()


@pytest.mark.freeze_time("2023-01-01")
def test_set_task_asignee(app, user, board):
    with app.app_context():
        other_user = User.create_user("other", b"password")
        board.set_user_role(user, other_user, "collaborator")

        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.set_assignee(user, other_user.id)
        assert task.assignee_id == other_user.id
        assert task.modified == 1672531200


@pytest.mark.freeze_time("2023-01-01")
def test_set_task_title(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.set_title(user, "foobar")
        assert task.title == "foobar"
        assert task.modified == 1672531200


@pytest.mark.freeze_time("2023-01-01")
def test_set_task_body(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )

        task = task.set_body(user, "foobar")
        assert task.body == "foobar"
        assert task.modified == 1672531200


def test_create_delete_task_tags(app, user, board):
    with app.app_context():
        task = board.new_task(
            creator=user,
            title="Task",
            body="",
        )
        task.add_tag(user, "test")
        assert TaskTag.select_task_tag(task.id, "test")

        task.remove_tag(user, "TEST")
        task = task.remove_tag(user, "TEST")

        assert len(task.tags) == 0
        assert TaskTag.select_task_tag(task.id, "test") is None


def test_task_fulltext_search(app, user, board, text_fixture_1, text_fixture_2):
    with app.app_context():
        extra_user = User.create_user("extra", b"user")
        extra_board = Board.new_board("EX", "extra", extra_user)
        extra_board.new_task(
            creator=extra_user,
            title="bork",
            body="bork",
        )

        for fixture in (text_fixture_1, text_fixture_2):
            title, body = fixture
            board.new_task(
                creator=user,
                title=title,
                body=body,
            )

        board = board.select_by_id(board.id)
        assert len(board.tasks) == 2
        assert len(task_search(user, "bork")) == 0
        assert len(task_search(user, "knowledge")) == 2
        assert len(task_search(user, "repentance")) == 1
        result = task_search(user, "NEAR(hopes pains)")[0]
        assert result[0] == 3
        assert result[1] == text_fixture_2[0]
        assert result[2] == text_fixture_2[1]
