import pytest
from flask import Flask, template_rendered
from flask.testing import (FlaskClient, FlaskCliRunner)

from src.app import create_app
from src.todo.auth.models import User


@pytest.fixture
def app() -> Flask:
    app = create_app("test_config.py")
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    client = app.test_client()
    with app.app_context():
        User.create_user(
            username="testuser",
            password=b"usertest",
        )
    with app.test_request_context():
        client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "usertest",
            }
        )
    yield client


@pytest.fixture
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture()
def runner(app: Flask) -> FlaskCliRunner:
    return app.test_cli_runner()
