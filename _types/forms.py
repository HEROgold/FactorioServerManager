from collections.abc import Generator
from typing import Any, Self

from flask_wtf.form import _Auto
import requests
from bs4 import BeautifulSoup
from flask_wtf import FlaskForm  # type: ignore[stub]
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email

from config import ARCHIVE_URL, LOWER_PORT_LIMIT, UPPER_PORT_LIMIT


def get_all_download_versions() -> list[str]:
    """Get all versions."""
    response = requests.get(ARCHIVE_URL, timeout=5)
    soup = BeautifulSoup(response.text, "html.parser")
    return ["latest", "stable"] + [
        i.text.strip()
        for i in soup.find_all("a", {"class": "slot-button-inline"})
    ]

used_ports: list[int] = []
def get_available_port() -> Generator[int, Any, None]:
    """Get an available port."""
    for i in range(LOWER_PORT_LIMIT, UPPER_PORT_LIMIT + 1):
        if i not in used_ports:
            used_ports.append(i)
            yield i

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    email_auth_code = PasswordField("Authentication Code")
    submit = SubmitField("Login")

class InstallForm(FlaskForm):
    name = StringField("Server Name", validators=[DataRequired()])
    port = IntegerField("UDP Port", validators=[DataRequired()], default=34197)
    version = SelectField("Version", validators=[DataRequired()], choices=[(i, i) for i in get_all_download_versions()])
    submit = SubmitField("Install")

class ManageServerForm(FlaskForm):
    port = IntegerField("UDP Port", validators=[DataRequired()]) # Make read-only

    # In game hosting options
    name = StringField("Server Name", validators=[DataRequired()])
    game_password = StringField("Password")

    description = StringField("Description")
    tags = StringField("Tags", default="")
    visibility_public = BooleanField("Public", default=False)
    visibility_steam = BooleanField("Steam", default=False)
    visibility_lan = BooleanField("LAN", default=True)

    require_user_verification = BooleanField("Verify User Identity", default=True)
    use_authserver_bans = BooleanField("Use Authserver Bans", default=True)
    whitelist = BooleanField("Whitelist", default=False)

    max_players = IntegerField("Max Players", default=10)
    ignore_limit_returning = BooleanField("Ignore Max Players For Returning Players", default=False)

    admins = StringField("Admins", default="")
    allow_commands = SelectField("Allow Lua Commands", default="admin-only", choices=[("false", "false"), ("admins-only", "admins-only"), ("true", "true")])
    only_admins_can_pause_the_game = BooleanField("Only Admins Can Pause The Game", default=True)
    afk_autokick_interval = IntegerField("AFK Autokick Timer", default=0)

    max_upload_in_kilobytes_per_second = IntegerField("Max Upload Speed", default=2000)
    max_upload_slots = IntegerField("Max Upload Slots", default=5)
    ignore_player_limit_for_returning_players = BooleanField("Ignore Player Limit For Returning Players", default=False)

    autosave_interval = IntegerField("Autosave Interval", default=3600)
    autosave_only_on_server = BooleanField("Autosave Only On Server", default=True)
    non_blocking_saving = BooleanField("Non Blocking Saving (Experimental?)", default=False)
    auto_pause = BooleanField("Auto Pause When There Are No Players Online", default=True)

    submit = SubmitField("Update settings")
