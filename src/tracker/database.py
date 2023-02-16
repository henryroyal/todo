import sqlite3
from threading import Lock

mutex = Lock()


class Database:
    def __init__(self, app):
        self.app = app
        self.path = None
        self.timeout = None

        self.path = self.app.config["DATABASE_PATH"]
        self.timeout = int(self.app.config.get("DATABASE_MUTEX_TIMEOUT", 30))
        self.connection = sqlite3.Connection(
            self.path,
            check_same_thread=False,
        )

        if not hasattr(self.app, "database"):
            setattr(self.app, "database", self)

    def __enter__(self):
        mutex.acquire(
            blocking=True,
            timeout=self.timeout,
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        mutex.release()
