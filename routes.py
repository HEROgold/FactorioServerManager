"""The module where some app level routes are defined."""

from typing import Literal

from flask import redirect, render_template, url_for
from werkzeug import Response

import blueprints  # type: ignore[no-stub-file]
from _types import Website


app = Website(__name__)


for bp in blueprints.all_blueprints:
    app.register_blueprint(bp)


@app.route("/")
async def index() -> Response:
    """Index page."""
    return redirect(url_for("dashboard.index"))


@app.errorhandler(404)
async def page_not_found(e: Exception) -> tuple[str, Literal[404]]:
    """Handle 404 errors."""
    return render_template("404.j2", error=e), 404
