"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, render_template
from flask_login import (
    current_user,  # type: ignore[reportAssignmentType]
)

from scripts import require_login


if TYPE_CHECKING:
    from _types.database import User
    current_user: "User"



this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")
bp.before_request(require_login)

@bp.route("/")
async def index() -> str:
    """Dashboard page."""
    return render_template("server/overview.j2", servers=current_user.servers.values())
