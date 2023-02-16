from os import environ

from src.tracker.migrator import Migration

MIGRATIONS = (
    Migration("auth", "0000_initial_tables.sql"),
    Migration("auth", "0001_permissions_seed.sql"),
    Migration("board", "0000_initial_tables.sql"),
    Migration("task", "0000_initial_tables.sql"),
)

SECRET_KEY = environ.get("SECRET_KEY", "development")  # fixme
PASSWORD_SALT = environ.get("PASSWORD_SALT", "Asalt")
ALLOW_NEW_ACCOUNTS = environ.get("ALLOW_NEW_ACCOUNTS", True)
DATABASE_PATH = environ.get("DATABASE_PATH", "todo.db")
DATABASE_MUTEX_TIMEOUT = int(environ.get("DATABASE_MUTEX_TIMEOUT", 30))

SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__todoapp"
SESSION_TYPE = "filesystem"
SESSION_USE_SIGNER = True
