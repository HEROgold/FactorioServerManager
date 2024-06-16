"""Blueprint for server management."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user  # type: ignore[reportAssignmentType]
from werkzeug import Response

from _types.data import Server
from _types.forms import ManageServerForm
from _types.settings import ServerSettings


if TYPE_CHECKING:
    from _types.database import User
    current_user: "User"

this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")

prefix = "/<string:name>"


@bp.route(prefix)
async def manage_server(name: str) -> str:
    """Manage a server page."""
    # TODO: show server logs
    server = current_user.servers[name]

    form = ManageServerForm(**server.settings.__dict__)
    return render_template("manage_server.j2", server=server, form=form)


@bp.route(prefix+"/update", methods=["POST"])
async def update_server(name: str) -> Response:
    """Update a server."""
    server = current_user.servers[name]
    form = ManageServerForm(request.form)
    server.settings = ServerSettings(**form.data)
    return redirect(url_for(".manage_server", name=name))


@bp.route(prefix+"/create", methods=["POST"])
async def create_server(name: str) -> Response:
    """Create a server."""
    version = request.form["version"]
    # only keep 0-9, a-z, A-Z, and _ in the name
    name = "".join([c for c in name if c.isalnum() or c == "_"])
    current_user.add_server(Server(name, current_user))
    server = current_user.servers[name]
    await server.create(version)
    return redirect(url_for(".manage_server", name=name))


@bp.route(prefix+"/delete", methods=["GET"])
async def delete_server(name: str) -> Response:
    """Delete a server."""
    server = current_user.servers[name]
    server.remove()
    return redirect(url_for(".index"))


@bp.route(prefix+"/start", methods=["POST"])
async def start_server(name: str) -> Response:
    """Start a server through a http request."""
    await current_user.servers[name].start()
    return Response(status=200)


@bp.route(prefix+"/stop", methods=["POST"])
async def stop_server(name: str) -> Response:
    """Stop a server through a http request."""
    await current_user.servers[name].stop()
    return Response(status=200)


@bp.route(prefix+"/restart", methods=["POST"])
async def restart_server(name: str) -> Response:
    """Restart a server through a http request."""
    await current_user.servers[name].restart()
    return Response(status=200)


@bp.route(prefix+"/rcon", methods=["POST", "GET"])
async def rcon(name: str) -> Response:
    """RCON page."""
    return Response(status=200)
