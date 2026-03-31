"""Blueprint for download page."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from flask import Blueprint, render_template
from flask_login import current_user

from FSM.scripts import require_login

if TYPE_CHECKING:
    from FSM._types.database import User



this_filename = Path(__file__).name.split(".")[0]
bp = Blueprint(this_filename, __name__, url_prefix=f"/{this_filename}")
bp.before_request(require_login)

@bp.route("/")
async def index() -> str:
    """Dashboard page."""
    user = cast(User, current_user)
    return render_template("server/overview.j2", servers=user.servers.values())
