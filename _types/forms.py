from flask_wtf import FlaskForm  # type: ignore[stub]
from wtforms import BooleanField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email

from _types.enums import Build, Distro
from scripts import get_all_download_versions, get_downloaded


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    email_auth_code = PasswordField("Authentication Code")
    submit = SubmitField("Login")

class DownloadForm(FlaskForm):
    build = SelectField("Build", validators=[DataRequired()], choices=[(i.name, i.name) for i in Build])
    distro = SelectField("Distro", validators=[DataRequired()], choices=[(i.name, i.name) for i in Distro])
    version = SelectField("Version", validators=[DataRequired()], choices=[(i, i) for i in get_all_download_versions()])
    submit = SubmitField("Download")

class InstallForm(FlaskForm):
    file = SelectField("File", validators=[DataRequired()], choices=[(i.name, i.name) for i in get_downloaded()])
    name = StringField("Server Name", validators=[DataRequired()])
    port = IntegerField("UDP Port", validators=[DataRequired()], default=34197)
    submit = SubmitField("Install")

class ManageServerForm(FlaskForm):
    name = StringField("Server Name", validators=[DataRequired()])
    port = IntegerField("UDP Port", validators=[DataRequired()])

    # In game hosting options
    display_name = StringField("Display Name")
    password = StringField("Password")

    description = StringField("Description")
    tags = StringField("Tags", default="")
    visibility_public = BooleanField("Public", default=False)
    visibility_steam = BooleanField("Steam", default=False)
    visibility_lan = BooleanField("LAN", default=True)

    verify_user_identity = BooleanField("Verify User Identity", default=True)
    use_authserver_bans = BooleanField("Use Authserver Bans", default=True)
    whitelist = BooleanField("Whitelist", default=False)

    max_players = IntegerField("Max Players", default=10)
    ignore_limit_returning = BooleanField("Ignore Max Players For Returning Players", default=False)

    admins = StringField("Admins", default="")
    allow_lua_commands = BooleanField("Allow Lua Commands", default=False)
    admin_pause = BooleanField("Only Admins Can Pause The Game", default=True)
    afk_autokick_timer = IntegerField("AFK Autokick Timer", default=0)

    max_upload_speed = IntegerField("Max Upload Speed", default=2000)
    max_upload_slots = IntegerField("Max Upload Slots", default=5)

    autosave_interval = IntegerField("Autosave Interval", default=3600)
    autosave_only_on_server = BooleanField("Autosave Only On Server", default=True)

    # Dedicated server specific options

    submit = SubmitField("Manage")
