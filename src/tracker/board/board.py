"""

Task Board module

"""
from datetime import datetime

from flask import Blueprint, Response, render_template, session, redirect, flash, request, abort, url_for
from src.tracker.auth.models import User, Role
from src.tracker.board.models import Board

board_bp = Blueprint(
    name="board_bp",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="assets",
)


@board_bp.app_template_filter()
def format_epoch_timestamp_as_date(ts: int) -> str:
    if ts is None:
        return "Never"
    parsed = datetime.fromtimestamp(ts)
    return parsed.strftime("%d/%m/%Y")


@board_bp.get("/")
def boards():
    """
    List boards associated with user
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    user_boards = Board.user_boards(user)

    return Response(
        response=render_template(
            "board/board_list.html",
            username=user.username,
            user_boards=user_boards,
        ),
    )


@board_bp.get("/<username>/<symbol>")
def board_detail_get(username: str, symbol: str):
    """
    Detail view of a specific board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(
        creator.id, symbol,
    )

    if user != board.creator and not board.user_can_view(user):
        flash("not authorized")
        return redirect("/")

    return Response(
        response=render_template(
            "board/board_detail.html",
            creator=creator,
            board=board,
        )
    )


@board_bp.post("/<username>/<symbol>")
def board_detail_post(username: str, symbol: str):
    """
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)
    name = request.form.get("name")
    symbol = request.form.get("symbol")
    status = request.form.get("status")

    if user != board.creator and not board.user_can_edit(user):
        flash("not authorized")
        return redirect("/")

    if name and name != board.name:
        board.rename_board(user, name)
    if symbol and symbol != board.symbol:
        board.set_board_symbol(user, symbol)
    if status and status != board.current_status.name:
        board.set_board_status(user, status)

    return redirect("/boards")


@board_bp.post("/<username>/<symbol>/delete")
def board_delete_post(username: str, symbol: str):
    """
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)

    if user != board.creator and not board.user_can_delete(user):
        flash("not authorized")
        return redirect("/")

    board.delete()
    return redirect("/boards")


@board_bp.get("/create")
def board_create_get():
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    return Response(
        response=render_template("board/board_create.html")
    )


@board_bp.post("/create")
def board_create_post():
    """
    Endpoint for creating a new board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    name = request.form["name"]
    symbol = request.form["symbol"]
    Board.new_board(
        name=name,
        symbol=symbol,
        creator=user,
    )

    return redirect("/boards")


@board_bp.get("/<username>/<symbol>/users")
def board_users_list_get(username: str, symbol: str):
    """

    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    if not creator:
        flash("unknown user")
        return redirect("/")

    board = Board.select_by_creator_symbol(creator.id, symbol)
    if not board:
        abort(404, "board not found")

    if user != board.creator and not board.user_can_view(user):
        flash("not authorized")
        return redirect("/")

    board_users = board.board_users_summary(creator)

    return Response(
        response=render_template(
            "board/board_users_list.html",
            view_name=f"User Shares",
            username=username,
            symbol=symbol,
            board_users=board_users,
        ),
    )


@board_bp.get("/<username>/<symbol>/users/share")
def board_users_share_get(username: str, symbol: str):
    """
    Detail view of a specific board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    if not creator:
        flash("unknown user")
        return redirect("/")

    board = Board.select_by_creator_symbol(creator.id, symbol)
    if not board:
        flash("unknown board")
        return redirect("/")

    if user != board.creator and not board.user_can_invite(user):
        flash("not authorized")
        return redirect("/")

    return Response(
        response=render_template(
            "board/board_users_share.html",
            username=username,
            symbol=symbol,
        ),
    )


@board_bp.post("/<username>/<symbol>/users/share")
def board_users_share_post(username: str, symbol: str):
    """
    Detail view of a specific board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    if not creator:
        flash("unknown user")
        return redirect("/")

    board = Board.select_by_creator_symbol(creator.id, symbol)
    if not board:
        flash("unknown board")
        return redirect("/")

    if user != board.creator and not board.user_can_invite(user):
        flash("not authorized")
        return redirect("/")

    form_grantee = request.form.get("grantee")
    form_role_name = request.form.get("role")

    owner = User.select_by_username(username)
    grantee = User.select_by_username(form_grantee)
    if not grantee:
        flash("sent invitation")
        return redirect(
            url_for("board_bp.board_users_list_get", username=username, symbol=symbol)
        )

    role = Role.select_by_name(form_role_name)
    board = Board.select_by_creator_symbol(owner.id, symbol)

    board.set_user_role(user, grantee, role.name)
    flash("sent invitation")
    return redirect(
        url_for("board_bp.board_users_list_get", username=username, symbol=symbol)
    )


@board_bp.post("/<username>/<symbol>/users/share/accept")
def board_users_share_accept_post(username: str, symbol: str):
    """
    Detail view of a specific board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)
    board.accept_user_role(user.id)
    return redirect(
        url_for("board_bp.boards")
    )


@board_bp.post("/<username>/<symbol>/users/share/decline")
def board_users_share_decline_post(username: str, symbol: str):
    """
    Detail view of a specific board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)
    board.decline_user_role(user.id)
    return redirect("/")
