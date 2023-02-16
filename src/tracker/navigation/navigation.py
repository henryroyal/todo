"""

Navigation and Boilerplate module

"""

from sqlite3 import OperationalError

from flask import Blueprint, render_template, Response, redirect, session, current_app, flash, request
from src.tracker.task.models import task_search
from src.tracker.auth.models import User
from src.tracker.board.models import Board

navigation_bp = Blueprint(
    name="navigation_bp",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="assets",
)


@navigation_bp.get("/")
def index():
    user = User.from_flask_session(session)
    allow_new_accounts = current_app.config.get("ALLOW_NEW_ACCOUNTS", True)

    share_requests = list()
    if user:
        share_requests = Board.list_user_share_requests_received(user)

    return Response(
        response=render_template(
            "navigation/index.html",
            user=user,
            share_requests=share_requests,
            allow_new_accounts=allow_new_accounts,
        )
    )


@navigation_bp.get("/search")
def search_get():
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")

    return redirect("/")


@navigation_bp.post("/search")
def search_post():
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    try:
        results = task_search(user, request.form["query"])
        flash(f"found {len(results)} results")
        if not results:
            return redirect("/")

    except OperationalError:
        flash("invalid query syntax")
        return redirect("/")

    return Response(
        response=render_template(
            "navigation/search_results.html",
            session=session,
            results=results,
        )
    )
