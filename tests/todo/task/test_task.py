import pytest

from src.todo.auth.models import User
from src.todo.board.models import Board
from src.todo.task.models import Task


@pytest.fixture
def board(app):
    with app.app_context():
        user = User.select_by_username("testuser")
        board = Board.new_board("TB", "Test Board", user)
        board.new_task(user, "Test Task #1", "Task Description", user)
        board.new_task(user, "Test Task #2", "Task Description", user)
        return board


def test_create_task_then_assign(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="otheruser",
            password=b"usertest",
        )
    with app.test_request_context():
        client.post(
            "/boards/create",
            data={
                "name": "hello board",
                "symbol": "HB"
            }
        )
        client.post(
            "/tasks/create",
            data={
                "board": "testuser/HB",
                "title": "test task",
                "description": "hello task"
            }
        )

    with app.app_context():
        user = User.select_by_username("testuser")
        other_user = User.select_by_username("otheruser")
        board = Board.select_by_creator_symbol(user.id, "HB")
        board.set_user_role(user, other_user, "collaborator")
        board.accept_user_role(other_user.id)

    with app.test_request_context():
        client.post(
            "/tasks/testuser/HB/1",
            data={
                "assignee": "otheruser",
            }
        )

    with app.app_context():
        users = board.board_users()
        assert len(users) == 2
        task = Task.select_by_board_and_number(board.id, 1)
        assert task.assignee_id == other_user.id


def test_add_comment_to_task(app, client, board, captured_templates):
    with app.test_request_context():
        client.post(
            "/tasks/testuser/TB/1/comment/new",
            data={
                "contents": "new comment",
            }
        )
        response = client.get(
            "/tasks/testuser/TB/1",
        )

        assert response.status_code == 200
        assert len(captured_templates[0][1]["task"].comments) == 1



# def test_add_existing_tag_to_task():
#     return


# def test_disaccociate_tag_with_single_association():
#     return


# def test_disaccociate_tag_with_multiple_associations():
#     return


# def test_managing_user_can_edit_and_delete():
#     return


# def test_creating_user_can_edit_and_delete():
#     return


# def test_non_creating_user_cannot_edit_or_delete():
#     return
