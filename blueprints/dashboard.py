"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator, NoReturn

from flask import Blueprint, redirect, render_template, request, stream_with_context, url_for
from flask_login import (
    current_user,  # type: ignore[reportAssignmentType]
    login_required,
)
from werkzeug import Response

from _types.data import Server
from _types.forms import InstallForm, ManageServerForm
from _types.settings import ServerSettings


if TYPE_CHECKING:
    from _types.database import User
    current_user: "User"



this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")


@bp.before_request
@login_required
async def before_request() -> None:
    """Run before every request."""
    return


@bp.route("/")
@bp.route("/index")
async def index() -> str:
    """Dashboard page."""
    return await server_overview()


@bp.route("/install_server/<string:name>", methods=["GET", "POST"])
async def install_server(name: str) -> Response | str:
    """Manage a server page."""
    if request.method == "GET":
        return render_template(
            "install_server.j2",
            form=InstallForm(),
            server_name=name,
        )
    if request.method == "POST":
        name = request.form["name"]
        return redirect(url_for(".create_server", name=name), code=307)
    return redirect(request.referrer, code=400)


@bp.route("/server_overview")
async def server_overview() -> str:
    """Manage servers page."""
    return render_template("server_overview.j2", servers=current_user.servers.values())


@bp.route("/manage_server/<string:name>")
async def manage_server(name: str) -> str:
    """Manage a server page."""
    # TODO: show server logs
    server = current_user.servers[name]

    form = ManageServerForm(**server.settings.__dict__)
    return render_template("manage_server.j2", server=server, form=form)

@bp.route("/manage_server/<string:name>/update", methods=["POST"])
async def update_server(name: str) -> Response:
    """Update a server."""
    server = current_user.servers[name]
    form = ManageServerForm(request.form)
    server.settings = ServerSettings(**form.data)
    return redirect(url_for(".manage_server", name=name))

@bp.route("/manage_server/<string:name>/create", methods=["POST"])
async def create_server(name: str) -> Response:
    """Create a server."""
    version = request.form["version"]
    # only keep 0-9, a-z, A-Z, and _ in the name
    name = "".join([c for c in name if c.isalnum() or c == "_"])
    current_user.add_server(Server(name, current_user))
    server = current_user.servers[name]
    await server.create(version)
    return redirect(url_for(".manage_server", name=name))


@bp.route("/manage_server/<string:name>/start", methods=["POST"])
async def start_server(name: str) -> Response:
    """Start a server through a http request."""
    await current_user.servers[name].start()
    return Response(status=200)

@bp.route("/manage_server/<string:name>/stop", methods=["POST"])
async def stop_server(name: str) -> Response:
    """Stop a server through a http request."""
    await current_user.servers[name].stop()
    return Response(status=200)


@bp.route("/manage_server/<string:name>/restart", methods=["POST"])
async def restart_server(name: str) -> Response:
    """Restart a server through a http request."""
    await current_user.servers[name].restart()
    return Response(status=200)


def get_live_server_status(name: str) -> str:
    """Get the status of a server. without using cached data."""
    return Server(name, current_user).status


@bp.route("/server_status/<string:name>")
def server_status(name: str) -> Response:
    """Stream the status of a server using SSE."""
    def generate() -> Generator[str, Any, NoReturn]:
        previous_status = None
        while True:
            status = get_live_server_status(name)
            if status == previous_status:
                continue
            previous_status = status
            yield "event: serverStatusUpdate\n"
            yield f"data: {status}\n"
            yield "\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream")
