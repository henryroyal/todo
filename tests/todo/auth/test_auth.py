import pytest

from src.todo.auth.models import User
from flask_wtf.csrf import generate_csrf


def test_invalid_password_login_post(app, client):
    """"""
    session_cookie_name = app. \
        session_interface.get_cookie_name(app)

    with app.app_context():
        with app.test_request_context():
            response = client.post(
                "/login",
                data={
                    "username": "testuser",
                    "password": "invalid",
                }
            )

        assert response.status_code == 302
        assert response.headers["Location"] == "/"

        with app.test_request_context():
            response = client.get(
                "/boards",
            )

        assert response.status_code == 308
        assert response.headers["Location"] == "http://localhost/boards/"


def test_create_user_get(client):
    response = client.get(
        "/signup"
    )

    assert response.status_code == 200


@pytest.mark.freeze_time("2023-01-01")
def test_create_new_user(app, client):
    session_cookie_name = app. \
        session_interface.get_cookie_name(app)

    with app.test_request_context():
        response = client.post(
            "/signup",
            data={
                "username": "newuser",
                "password": "test123",
                "password_confirmation": "test123",
            }
        )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert session_cookie_name in response.headers["Set-Cookie"]

    with app.app_context():
        user = User.select_by_username("newuser")

    assert user.username == "newuser"
    assert user.is_admin is False
    assert user.is_active is True
    assert user.created == 1672531200
    assert user.modified is None


def test_create_admin_user(app):
    with app.app_context():
        user = User.create_admin("admin", b"password")
        assert user.username == "admin"
        assert user.is_admin is True
        assert user.is_active is True

# def test_settings_get(client):
#     response = client.get(
#         "/settings"
#     )
#     assert response.status_code == 200

# def test_deactivate_reactivate_user():
#     return


# def test_admin_accesses_admin_tools():
#     return

# def test_non_admin_cannit_access_admin_tools():
#     return

# def test_change_user_password():
#     return

# def test_authenticate_user_password():
#     return

# def test_authorize_authorized_user():
#     return

# def test_reject_unauthorized_user():
#     return
