# noqa: D100

import secrets
from pathlib import Path
from tomllib import load


# Users may edit these
REQUIRE_GAME_OWNERSHIP = False


# Do not edit
CONFIG_FILE = Path(__file__)
TOML_FILE = CONFIG_FILE.parent / "pyproject.toml"

with TOML_FILE.open("rb") as file:
    toml = load(file)

PROJECT_DIRECTORY = CONFIG_FILE.parent
SERVERS_DIRECTORY = CONFIG_FILE.parent / "servers"
DOWNLOADS_DIRECTORY = CONFIG_FILE.parent / "downloads"

DATABASE_PATH = CONFIG_FILE.parent / "database.db"

PROJECT_NAME = toml["project"]["name"]
PROJECT_VERSION = toml["project"]["version"]
SECRET_KEY = secrets.token_hex(64)
API_VERSION = 4

MODS_API_URL = "https://mods.factorio.com/api/mods"
LOGIN_URL = "https://www.factorio.com/login"
LOGIN_API = "https://auth.factorio.com/api-login"
RELEASES_URL = "https://factorio.com/api/latest-releases"
ARCHIVE_URL = "https://www.factorio.com/download/archive"
AVAILABLE_UPDATES_URL = "https://updater.factorio.com/get-available-versions."
SHA256SUMS_URL = "https://www.factorio.com/download/sha256sums/"

# Endpoints

# Login
L = "/login"
L_REGISTER = f"{L}/register"
L_DELETE = f"{L}/delete"
L_LOGIN = f"{L}/login"
L_LOGOUT = f"{L}/logout"

# Files
F = "/files"
F_GET_ALL = f"{F}/get_all"
F_GET = f"{F}/get"
F_CREATE = f"{F}/create"
F_UPDATE = f"{F}/update"
F_DELETE = f"{F}/delete"
