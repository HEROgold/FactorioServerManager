from flask_wtf import FlaskForm  # type: ignore[stub]
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email

from _types.enums import Build, Distro
from scripts import get_all_download_versions


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

