import pytest

from src.tracker.auth.models import User
from src.tracker.board.models import Board, BoardSummary


def test_boards_list_get_empty(app, client, captured_templates):
    response = client.get(
        "/boards/"
    )

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["username"] == "testuser"
    assert context["user_boards"] == list()


@pytest.mark.freeze_time("2023-01-01")
def test_boards_list_get_single_board(app, client, captured_templates):
    with app.app_context():
        user = User.select_by_username("testuser")
        Board.new_board("TST", "test board", user)

    response = client.get(
        "/boards/"
    )

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["username"] == "testuser"
    assert len(context["user_boards"]) == 1
    assert context["user_boards"][0] == BoardSummary(
        id=1, symbol='TST', name='test board', status='todo', creator_id=1,
        creator='testuser', role='manager', last_updated=1672531200,
        task_count=0, user_count=0
    )


@pytest.mark.freeze_time("2023-01-01")
def test_boards_list_boards(app, client, captured_templates):
    """
    board_one
      - user_one
      - user_two
      - user_three

    board_two
      - user_two
      - user_three

    board_three
      - user_three

    board_four
      - user_three
      - user_one

    bourd_five
      - user_three
      - user_two
    """
    with app.app_context():
        user_one = User.select_by_username("testuser")
        user_two = User.create_user("two", b"pwd")
        user_three = User.create_user("three", b"pwd")

        board_one = Board.new_board("B1", "board one", user_one)
        board_one.set_user_role(user_one, user_two, "collaborator")
        board_one.set_user_role(user_one, user_three, "collaborator")
        board_one.accept_user_role(user_two.id)
        board_one.accept_user_role(user_three.id)

        board_two = Board.new_board("B2", "board two", user_two)
        board_two.set_user_role(user_one, user_two, "collaborator")
        board_two.accept_user_role(user_two.id)

        board_three = Board.new_board("B3", "board three", user_three)
        board_three.accept_user_role(user_three.id)

        board_four = Board.new_board("B4", "board four", user_three)
        board_three.set_user_role(user_one, user_one, "viewer")
        board_four.accept_user_role(user_one.id)

        board_five = Board.new_board("B5", "board five", user_three)
        board_three.set_user_role(user_one, user_two, "viewer")
        board_five.accept_user_role(user_two.id)

    with app.test_request_context():
        client.get(
            "/boards/"
        )
        context = captured_templates[0][1]
        assert len(context["user_boards"]) == 1
        assert context["user_boards"][0] == BoardSummary(
            id=1, symbol='B1', name='board one', status='todo',
            creator_id=1, creator='testuser', role='manager',
            last_updated=1672531200, task_count=0, user_count=2)

    with app.test_request_context():
        client.post(
            "/login",
            data={
                "username": "two",
                "password": "pwd",
            }
        )
        client.get(
            "/boards/"
        )
        context = captured_templates[1][1]
        assert context["username"] == "two"
        assert len(context["user_boards"]) == 2
        assert context["user_boards"][0] == BoardSummary(
            id=2, symbol='B1', name='board one', status='todo',
            creator_id=1, creator='testuser', role='collaborator',
            last_updated=1672531200, task_count=0, user_count=2)
        assert context["user_boards"][1] == BoardSummary(
            id=4, symbol='B2', name='board two', status='todo',
            creator_id=2, creator='two', role='collaborator',
            last_updated=1672531200, task_count=0, user_count=0)

    with app.test_request_context():
        client.post(
            "/login",
            data={
                "username": "three",
                "password": "pwd",
            }
        )
        client.get(
            "/boards/"
        )
        context = captured_templates[2][1]
        assert len(context["user_boards"]) == 4
        assert context["user_boards"][0] == BoardSummary(
            id=3, symbol='B1', name='board one', status='todo',
            creator_id=1, creator='testuser', role='collaborator',
            last_updated=1672531200, task_count=0, user_count=2)
        assert context["user_boards"][1] == BoardSummary(
            id=6, symbol='B3', name='board three', status='todo',
            creator_id=3, creator='three', role='manager',
            last_updated=1672531200, task_count=0, user_count=0)
        assert context["user_boards"][2] == BoardSummary(
            id=7, symbol='B4', name='board four', status='todo',
            creator_id=3, creator='three', role='manager',
            last_updated=1672531200, task_count=0, user_count=0)
        assert context["user_boards"][3] == BoardSummary(
            id=9, symbol='B5', name='board five', status='todo',
            creator_id=3, creator='three', role='manager',
            last_updated=1672531200, task_count=0, user_count=0)


@pytest.mark.freeze_time("2023-01-01")
def test_board_create_update(app, client, captured_templates):
    with app.test_request_context():
        client.post(
            "/boards/create",
            data={
                "name": "hello board",
                "symbol": "HB"
            }
        )

    with app.test_request_context():
        client.post(
            "/boards/testuser/HB",
            data={
                "symbol": "foo",
                "name": "bar",
            }
        )

    with app.test_request_context():
        client.get(
            "/boards/"
        )
        context = captured_templates[0][1]
        assert len(context["user_boards"]) == 1
        assert context["user_boards"][0] == BoardSummary(
            id=1, symbol='foo', name='bar', status='todo', creator_id=1,
            creator='testuser', role='manager', last_updated=1672531200,
            task_count=0, user_count=0)


def test_board_delete(app, client, captured_templates):
    with app.test_request_context():
        client.post(
            "/boards/create",
            data={
                "name": "hello board",
                "symbol": "HB"
            }
        )
    with app.test_request_context():
        client.post(
            "/boards/testuser/HB/delete",
        )
        client.get(
            "/boards/"
        )
        context = captured_templates[0][1]
        assert len(context["user_boards"]) == 0


def test_board_update_status(app, client, captured_templates):
    with app.test_request_context():
        client.post(
            "/boards/create",
            data={
                "name": "hello board",
                "symbol": "HB"
            }
        )
        client.post(
            "/boards/testuser/HB",
            data={
                "status": "in-progress",
            }
        )
        client.get(
            "/boards/"
        )
        assert captured_templates[0][1]["user_boards"][0].status \
               == "in-progress"


def test_board_unauthorized_detail_get(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="unauthorized",
            password=b"test",
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
            "/login",
            data={
                "username": "unauthorized",
                "password": "test",
            }
        )
        response = client.get(
            "/boards/testuser/HB"
        )

        assert response.status_code == 302
        assert response.location == "/"


def test_board_unauthorized_detail_post(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="unauthorized",
            password=b"test",
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
            "/login",
            data={
                "username": "unauthorized",
                "password": "test",
            }
        )
        response = client.post(
            "/boards/testuser/HB",
            data={
                "name": "test board",
            }
        )

        assert response.status_code == 302
        assert response.location == "/"


def test_board_unauthorized_delete(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="unauthorized",
            password=b"test",
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
            "/login",
            data={
                "username": "unauthorized",
                "password": "test",
            }
        )
        response = client.post(
            "/boards/testuser/HB/delete",
        )

        assert response.status_code == 302
        assert response.location == "/"


def test_board_unauthorized_users_list_get(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="unauthorized",
            password=b"test",
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
            "/login",
            data={
                "username": "unauthorized",
                "password": "test",
            }
        )
        response = client.get(
            "/boards/testuser/HB/users",
        )

        assert response.status_code == 302
        assert response.location == "/"


def test_board_users_share_get(app, client, captured_templates):
    with app.app_context():
        User.create_user(
            username="unauthorized",
            password=b"test",
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
            "/login",
            data={
                "username": "unauthorized",
                "password": "test",
            }
        )
        response = client.get(
            "/boards/testuser/HB/users/share",
        )

        assert response.status_code == 302
        assert response.location == "/"
