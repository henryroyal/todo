import pytest
from src.tracker.auth.models import User
from src.tracker.board.models import Board, BoardStatus
from src.tracker.task.models import Task


@pytest.mark.freeze_time("2023-01-01")
def test_new_board(app):
    with app.app_context():
        user = User.create_user("test", b"test")
        board = Board.new_board("TST", "test board", user)

        assert board.symbol == "TST"
        assert board.name == "test board"
        assert board.creator.id == user.id
        assert board.created == 1672531200
        assert board.modified is None


def test_select_board_by_id(app):
    with app.app_context():
        user = User.create_user("test", b"test")
        board = Board.new_board("TST", "test board", user)
        board_by_id = Board.select_by_id(board.id)
        assert board.id == board_by_id.id
        assert board.name == board_by_id.name
        assert board.symbol == board_by_id.symbol
        assert board.current_status.name == board_by_id.current_status.name


def test_delete_board(app):
    with app.app_context():
        user = User.create_user("test", b"test")
        board = Board.new_board("TST", "test board", user)
        assert len(board.possible_statuses) == 2
        assert board.current_status not in board.possible_statuses
        assert board.current_status.name == "todo"

        task_one = board.new_task(
            creator=user,
            title="first task",
            body="1.) build",
            assignee=user,
        )
        task_two = board.new_task(
            creator=user,
            title="second task",
            body="2.) test",
            assignee=None,
        )
        board = Board.select_by_id(board.id)
        assert len(board.tasks) == 2
        board.delete()

        assert Board.select_by_id(board.id) is None
        assert Task.select_by_board_and_number(board.id, task_one.number) is None
        assert Task.select_by_board_and_number(board.id, task_two.number) is None
        assert BoardStatus.select_by_board_id(board.id) == list()


def test_rename_board(app):
    with app.app_context():
        user = User.create_user("test", b"test")
        board = Board.new_board("TST", "test board", user)
        board = board.rename_board(user, "renamed test board")
        assert board.name == "renamed test board"


def test_set_board_status(app):
    with app.app_context():
        user = User.create_user("test", b"test")
        board = Board.new_board("TST", "test board", user)
        assert board.current_status.name == "todo"
        board = board.set_board_status(user, "completed")
        assert board.current_status.name == "completed"


def test_add_set_delete_board_user(app):
    with app.app_context():
        user_one = User.create_user("first", b"user")
        user_two = User.create_user("second", b"user")
        board = Board.new_board("TST", "test board", user_one)
        board.set_user_role(user_one, user_two, "manager")
        assert board.get_user_role(user_one, user_two).role_name == "manager"
        board.set_user_role(user_one, user_two, "collaborator")
        assert board.get_user_role(user_one, user_two).role_name == "collaborator"
        board.set_user_role(user_one, user_two, "viewer")
        assert board.get_user_role(user_one, user_two).role_name == "viewer"
        board.delete_user_role(user_one, user_two)
        assert board.get_user_role(user_one, user_two) is None


def test_fetch_user_boards(app):
    with app.app_context():
        # three users
        user_one = User.create_user("first", b"user")
        user_two = User.create_user("second", b"user")
        user_three = User.create_user("third", b"user")

        # three boards belonging to user 1
        board_one = Board.new_board("B1", "Board #1", user_one)
        board_two = Board.new_board("B2", "Board #2", user_one)
        board_three = Board.new_board("B3", "Board #3", user_one)

        # grant collaborator on board #1 to user #2
        board_one.set_user_role(user_one, user_two, "collaborator")

        # user #2 accepts share
        board_one.accept_user_role(user_two.id)

        # board #3 has no users
        board_three.delete_user_role(user_one, user_one)

        assert len(Board.user_boards(user_one)) == 2
        assert len(Board.user_boards(user_two)) == 1
        assert len(Board.user_boards(user_three)) == 0


def test_update_board_symbol(app):
    with app.app_context():
        user = User.create_user("first", b"user")
        board = Board.new_board("?", "Board", user)
        board = board.set_board_symbol(user, "B")
        assert board.symbol == "B"


def test_board_user_view_permission(app):
    with app.app_context():
        unauthorized = User.create_user("unauth", b"user")
        viewer = User.create_user("viewer", b"user")
        creator = User.create_user("auth", b"user")

        board = Board.new_board("B", "Board", creator)
        assert board.user_can_view(viewer) is False
        board.set_user_role(creator, viewer, "viewer")
        assert board.user_can_view(viewer) is False
        board.accept_user_role(viewer.id)

        assert board.user_can_view(creator) is True
        assert board.user_can_view(viewer) is True
        assert board.user_can_view(unauthorized) is False


def test_board_user_create_permission(app):
    with app.app_context():
        unauthorized = User.create_user("unauth", b"user")
        collaborator = User.create_user("collab", b"user")
        creator = User.create_user("auth", b"user")
        board = Board.new_board("B", "Board", creator)

        assert board.user_can_create(collaborator) is False
        board.set_user_role(creator, collaborator, "collaborator")
        assert board.user_can_create(collaborator) is False
        board.accept_user_role(collaborator.id)
        assert board.user_can_create(collaborator) is True

        assert board.user_can_create(creator) is True
        assert board.user_can_create(unauthorized) is False


def test_board_user_edit_permission(app):
    with app.app_context():
        unauthorized = User.create_user("unauth", b"user")
        collaborator = User.create_user("collab", b"user")
        creator = User.create_user("auth", b"user")
        board = Board.new_board("B", "Board", creator)

        assert board.user_can_edit(collaborator) is False
        board.set_user_role(creator, collaborator, "collaborator")
        assert board.user_can_edit(collaborator) is False
        board.accept_user_role(collaborator.id)
        assert board.user_can_edit(collaborator) is True

        assert board.user_can_edit(creator) is True
        assert board.user_can_edit(unauthorized) is False


def test_board_user_delete_permission(app):
    with app.app_context():
        unauthorized = User.create_user("unauth", b"user")
        collaborator = User.create_user("collab", b"user")
        creator = User.create_user("auth", b"user")
        board = Board.new_board("B", "Board", creator)

        assert board.user_can_delete(collaborator) is False
        board.set_user_role(creator, collaborator, "collaborator")
        assert board.user_can_delete(collaborator) is False
        board.accept_user_role(collaborator.id)
        assert board.user_can_delete(collaborator) is True

        assert board.user_can_delete(creator) is True
        assert board.user_can_delete(unauthorized) is False


def test_board_user_invite_permission(app):
    with app.app_context():
        unauthorized = User.create_user("unauth", b"user")
        manager = User.create_user("collab", b"user")
        creator = User.create_user("auth", b"user")
        board = Board.new_board("B", "Board", creator)

        board.set_user_role(creator, unauthorized, "collaborator")
        board.accept_user_role(unauthorized.id)
        assert board.user_can_invite(unauthorized) is False

        assert board.user_can_invite(manager) is False
        board.set_user_role(creator, manager, "manager")
        assert board.user_can_invite(manager) is False
        board.accept_user_role(manager.id)
        assert board.user_can_invite(manager) is True

        assert board.user_can_invite(creator) is True
