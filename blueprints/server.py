"""Blueprint for server management."""

import contextlib
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

import docker.errors
from flask import Blueprint, redirect, render_template, request, stream_with_context, url_for
from flask_login import current_user  # type: ignore[reportAssignmentType]
from werkzeug import Response

from _types.data import Server
from _types.forms import InstallForm, ManageServerForm, get_available_port
from _types.settings import ServerSettings
from scripts import require_login, sanitize_str


if TYPE_CHECKING:
    from _types.database import User
    current_user: "User"

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")
bp.before_request(require_login)

prefix = "/<string:name>"
templates = "server"


def get_live_status(name: str) -> str:
    """Get the status of a server. without using cached data."""
    return Server(name, current_user).status


@bp.route("/")
@bp.route(prefix)
async def index(name: str) -> str:
    """Manage a server page."""
    # TODO: show server logs
    server = current_user.servers[name]
    settings = ServerSettings.read(server.custom_settings_file)

    form = ManageServerForm(**settings.__dict__)
    return render_template(templates+"/manage.j2", server=server, form=form)


@bp.route(prefix+"/install/", methods=["GET", "POST"])
async def install(name: str) -> Response | str:
    """Manage a server page."""
    if request.method == "GET":
        form: InstallForm = InstallForm()
        form.port.data = next(get_available_port())
        return render_template(
            templates+"/install.j2",
            form=form,
            server_name=name,
        )
    if request.method == "POST":
        name = request.form["name"]
        return redirect(url_for(".create", name=name), code=307)
    return redirect(request.referrer, code=400)


@bp.route(prefix+"/create", methods=["POST"])
async def create(name: str) -> Response:
    """Create a server."""
    version = request.form["version"]
    name = sanitize_str(name)

    server = Server(name, current_user)
    server.settings.port = int(request.form["port"])
    current_user.add_server(server)

    server = current_user.servers[name]
    await server.create(version)
    return redirect(url_for(".index", name=name))

@bp.route(prefix+"/update", methods=["POST"])
async def update(name: str) -> Response:
    """Update a server."""
    server = current_user.servers[name]
    form = ManageServerForm(request.form)
    server.settings = ServerSettings(**form.data)
    server.settings.write(server.custom_settings_file)
    return redirect(url_for(".index", name=name))


@bp.route(prefix+"/delete", methods=["GET"])
async def delete(name: str) -> Response:
    """Delete a server."""
    server = current_user.servers[name]
    with contextlib.suppress(docker.errors.NotFound):
        server.remove()
    return redirect(url_for("dashboard.index"))


@bp.route(prefix+"/start", methods=["POST"])
async def start(name: str) -> Response:
    """Start a server through a http request."""
    await current_user.servers[name].start()
    return Response(status=200)


@bp.route(prefix+"/stop", methods=["POST"])
async def stop(name: str) -> Response:
    """Stop a server through a http request."""
    await current_user.servers[name].stop()
    return Response(status=200)


@bp.route(prefix+"/restart", methods=["POST"])
async def restart(name: str) -> Response:
    """Restart a server through a http request."""
    try:
        await current_user.servers[name].restart()
    except RuntimeError as e:
        return Response(status=400, response=str(e))
    return Response(status=200)


@bp.route(prefix+"/status/")
def status(name: str) -> Response:
    """Stream the status of a server using SSE."""
    def generate() -> Generator[str, Any, NoReturn]:
        previous_status = None
        while True:
            status = get_live_status(name)
            if status == previous_status:
                continue
            previous_status = status
            yield "event: serverStatusUpdate\n"
            yield f"data: {status}\n"
            yield "\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream")


@bp.route(prefix+"/rcon", methods=["POST", "GET"])
async def rcon(name: str) -> Response:
    """RCON page."""
    return Response(status=200)
