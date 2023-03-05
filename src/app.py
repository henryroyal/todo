"""

#todo app

"""
from typing import Optional

from flask import Flask
from flask_session import Session
from flask_wtf import CSRFProtect

from src.todo.auth.auth import auth_bp
from src.todo.board.board import board_bp
from src.database import Database
from src.migrator import Migrator
from src.todo.navigation.navigation import navigation_bp
from src.todo.task.task import task_bp


def create_app(config_filename: Optional[str]) -> Flask:
    app = Flask(__name__)

    if config_filename:
        app.config.from_pyfile(config_filename)

    CSRFProtect(app)
    Session(app)
    Database(app)

    with app.database as conn:
        migrator = Migrator()
        migrator.init_migrations(conn)

        migrations = app.config["MIGRATIONS"]
        migrator.apply_migrations(
            conn, migrations
        )

    app.register_blueprint(navigation_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(board_bp, url_prefix="/boards")
    app.register_blueprint(task_bp, url_prefix="/tasks")

    return app
