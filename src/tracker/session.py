from flask_session import Session
from flask_session.sessions import SessionInterface


class AppSessionInterface(SessionInterface):
    def __init__(self):
        super().__init__()

    def open_session(self, app, request):
        return None


class AppSession(Session):
    def __init__(self, app):
        super().__init__(app)

    def _get_interface(self, app):
        config = app.config.copy()
        return AppSessionInterface()
