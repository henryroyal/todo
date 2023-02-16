"""

Auth module

"""

from datetime import datetime

from flask import (
    current_app,
    render_template,
    Blueprint,
    redirect,
    request,
    Response,
    session,
    flash,
)

from .models import User

auth_bp = Blueprint(
    name="auth_bp",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="assets",
)


@auth_bp.app_template_filter()
def format_epoch_timestamp_as_datetime(ts) -> str:
    if ts is None:
        return "Never"
    parsed = datetime.fromtimestamp(ts)
    return parsed.strftime("%d/%m/%Y %-I:%M:%S %p UTC")


@auth_bp.post("/login")
def login_post():
    """
    Handle auth requests, return
    response with session cookie
    if successful.
    """
    user = User.select_by_username(request.form["username"])
    guessed_password = bytes(request.form["password"], "utf8")

    if not user or not user.verify_password(guessed_password):
        flash("login failed")
        if "username" in session:
            del session["username"]

        return redirect(location="/")

    session["username"] = user.username
    return redirect(location="/")


@auth_bp.get("/logout")
def logout_get():
    """
    Invalidate session and redirect to index
    """
    if "username" in session:
        del session["username"]
    return redirect(location="/")


@auth_bp.post("/signup")
def signup_post():
    """
    Create a new user
    """
    username = request.form["username"]
    password = request.form["password"]
    password_confirmation = request.form["password_confirmation"]

    if password != password_confirmation:
        flash("password & confirmation must be identical")
        return redirect("/")

    existing_user = User.select_by_username(username)
    if existing_user:
        flash("username is taken")
        return redirect("/")

    new_user = User.create_user(
        username=username,
        password=bytes(password, "utf8"),
    )

    session["username"] = new_user.username
    flash("user created")
    return redirect("/")


@auth_bp.get("/signup")
def signup_get():
    """
    New user form
    """
    return Response(
        response=render_template("auth/signup.html")
    )


@auth_bp.get("/settings")
def settings_get():
    """
    Return user settings panel
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please log in")
        return redirect("/")

    all_users = None
    if user.is_admin:
        all_users = User.all_users_for_admin()

    return Response(
        response=render_template(
            "auth/settings.html",
            current_user=user,
            all_users=all_users,
        )
    )


@auth_bp.post("/settings")
def settings_post():
    """
    Modify user settings
    """
    return Response(response=render_template("auth/settings.html"))
