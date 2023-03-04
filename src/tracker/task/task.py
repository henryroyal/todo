"""

Task module

"""

from datetime import datetime
from flask import Blueprint, render_template, Response, redirect, session, flash, request, url_for, abort
from src.tracker.auth.models import User
from src.tracker.board.models import Board
from src.tracker.task.models import Task

task_bp = Blueprint(
    name="task_bp",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="assets",
)


@task_bp.app_template_filter()
def format_epoch_timestamp_as_date(ts: int) -> str:
    if ts is None:
        return "Never"
    parsed = datetime.fromtimestamp(ts)
    return parsed.strftime("%d/%m/%Y")


@task_bp.get("/")
def tasks():
    user = User.from_flask_session(session)
    if not user:
        flash("please log in")
        return redirect("/")

    user_tasks = Task.user_tasks(user)

    return Response(
        response=render_template(
            "task/task_list.html",
            tasks=user_tasks,
            view_name="Tasks"
        ),
    )


@task_bp.get("/<username>/<symbol>")
def tasks_by_board(username: str, symbol: str):
    """
    List tasks related to board
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please log in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)
    board_tasks = board.board_tasks(user, board.id)

    if not board.user_can_view(user):
        flash("not authorized")
        return redirect("/")

    return Response(
        response=render_template(
            "task/task_list.html",
            tasks=board_tasks,
            view_name=f"{board.symbol} Tasks"
        ),
    )


@task_bp.get("/<username>/<symbol>/<number>")
def tasks_detail_get(username: str, symbol: str, number: int):
    """
    Detail view for task
    """
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)

    if user != board.creator and not board.user_can_view(user):
        flash("not authorized")
        return redirect("/")

    task = board.get_task(number)

    assignee_username = None
    if task.assignee_id:
        assignee = User.select_by_id(task.assignee_id)
        assignee_username = assignee.username

    possible_assignees = [
        name for name in board.board_users()
    ]

    return Response(
        response=render_template(
            "task/task_detail.html",
            creator=creator,
            board=board,
            task=task,
            assignee=assignee_username,
            possible_assignees=possible_assignees,
        )
    )


@task_bp.post("/<username>/<symbol>/<number>")
def task_detail_post(username: str, symbol: str, number: int):
    """
    Endpoint for modifying task details
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
    if user != board.creator and not board.user_can_edit(user):
        flash("not authorized")
        return redirect("/")

    form = request.form
    task = Task.select_by_board_and_number(board.id, number)

    assignee = None
    assignee_username = form.get("assignee")
    if assignee_username:
        assignee = User.select_by_username(assignee_username)

    assignee_id = None
    if assignee:
        assignee_id = assignee.id

    if task.assignee_id != assignee_id:
        task.set_assignee(user, assignee_id)

    title = form.get("title")
    if title and task.title != title:
        task.set_title(user, title)

    status = form.get("status")
    if task.status:
        current_status = task.status.name
    else:
        current_status = None

    if status and current_status != status:
        task.set_status(user, status)

    body = form.get("body")
    if body and task.body != body:
        task.set_body(user, body)

    possible_assignees = [
        name for name in board.board_users()
    ]

    return redirect(
        url_for(
            "task_bp.tasks_detail_get",
            username=username,
            symbol=symbol,
            number=number,
            assignee=assignee,
            possible_assignees=possible_assignees,
        )
    )


@task_bp.get("/create")
def task_create_get():
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    user_boards = Board.user_boards(user)

    return Response(
        response=render_template(
            "task/task_create.html",
            user_boards=user_boards,
        ),
    )


@task_bp.post("/create")
def task_create_post():
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    board = request.form.get("board")
    if not board:
        abort(400, "board ID is required")

    board_creator, board_symbol = board.split("/")
    creator = User.select_by_username(board_creator)
    if not creator:
        abort(400, "board not found")

    board = Board.select_by_creator_symbol(creator.id, board_symbol)
    if not board:
        abort(404, "board not found")

    if user != board.creator and not board.user_can_edit(user):
        flash("not authorized")
        return redirect("/")

    title = request.form.get("title", "")
    body = request.form.get("description", "")
    assignee = request.form.get("assignee", None)
    board.new_task(user, title, body, assignee)
    return redirect("/tasks")


@task_bp.post("/<username>/<symbol>/<number>/comment/new")
def task_new_comment(username: str, symbol: str, number: int):
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)

    if user != board.creator and not board.user_can_edit(user):
        flash("not authorized")
        return redirect("/")

    contents = request.form.get("contents", "")
    board.get_task(number).new_comment(user, contents)
    return redirect(
        url_for(
            "task_bp.tasks_detail_get",
            username=username,
            symbol=symbol,
            number=number,
        )
    )


@task_bp.post("/<username>/<symbol>/<number>/comment/<comment>/delete")
def task_delete_comment(username: str, symbol: str, number: int, comment: int):
    user = User.from_flask_session(session)
    if not user:
        flash("please sign in")
        return redirect("/")

    creator = User.select_by_username(username)
    board = Board.select_by_creator_symbol(creator.id, symbol)
    if user != board.creator and not board.user_can_edit(user):
        flash("not authorized")
        return redirect("/")

    board.get_task(number).delete_comment(user, comment)
    flash("deleted comment")
    return redirect(
        url_for(
            "task_bp.tasks_detail_get",
            username=username,
            symbol=symbol,
            number=number,
        )
    )
