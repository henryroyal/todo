from os import environ
from distutils.util import strtobool

from src.migrator import Migration

MIGRATIONS = (
    Migration("todo", "auth", "0000_initial_tables.sql"),
    Migration("todo", "auth", "0001_permissions_seed.sql"),
    Migration("todo", "board", "0000_initial_tables.sql"),
    Migration("todo", "task", "0000_initial_tables.sql"),
)

SECRET_KEY = environ["SECRET_KEY"]
PASSWORD_SALT = environ["PASSWORD_SALT"]
SESSION_COOKIE_DOMAIN = environ.get("SESSION_COOKIE_DOMAIN")
ALLOW_NEW_ACCOUNTS = strtobool(environ.get("ALLOW_NEW_ACCOUNTS", "1"))
DATABASE_PATH = environ.get("DATABASE_PATH", "todo.db")
DATABASE_MUTEX_TIMEOUT = int(environ.get("DATABASE_MUTEX_TIMEOUT", 30))

SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__todoapp"
SESSION_TYPE = "filesystem"
SESSION_USE_SIGNER = True
