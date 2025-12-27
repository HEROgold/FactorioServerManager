# noqa: D100

import os
import secrets
from configparser import ConfigParser
from pathlib import Path

from confkit import Config

# Users may edit these
REQUIRE_GAME_OWNERSHIP = False
PUBLIC_IP = "x.x.x.x" # The IP Address where servers are reachable from.


# Do not edit
CONFIG_FILE = Path(__file__)
PROJECT_DIR = CONFIG_FILE.parent
TOML_FILE = PROJECT_DIR / "pyproject.toml"

Config.set_parser(ConfigParser())
Config.set_file(PROJECT_DIR/"config.ini")

DOCKER_CONTAINER_PREFIX = "factorio-headless"

PROJECT_DIRECTORY = PROJECT_DIR
SERVERS_DIRECTORY = PROJECT_DIR / "servers"
DOWNLOADS_DIRECTORY = PROJECT_DIR / "downloads"
SAVES_DIRECTORY = PROJECT_DIR / "saves"

DATABASE_PATH = PROJECT_DIR / "database.db"

SECRET_KEY_ENV = "FSM_SECRET_KEY"  # noqa: S105
SECRET_KEY_FILE = PROJECT_DIR / ".flask_secret.key"


def _load_secret_key() -> str:
    env_value = os.getenv(SECRET_KEY_ENV)
    if env_value:
        return env_value.strip()

    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_text(encoding="utf-8").strip()

    key = secrets.token_hex(64)
    SECRET_KEY_FILE.write_text(key, encoding="utf-8")
    try:
        if os.name != "nt":
            SECRET_KEY_FILE.chmod(0o600)
    except OSError:
        # Permission tweaks may fail on some filesystems; silently continue.
        pass
    return key


SECRET_KEY = _load_secret_key()
API_VERSION = 4

MODS_API_URL = "https://mods.factorio.com/api/mods"
LOGIN_URL = "https://www.factorio.com/login"
LOGIN_API = "https://auth.factorio.com/api-login"
RELEASES_URL = "https://factorio.com/api/latest-releases"
ARCHIVE_URL = "https://www.factorio.com/download/archive"
AVAILABLE_UPDATES_URL = "https://updater.factorio.com/get-available-versions."
SHA256SUMS_URL = "https://www.factorio.com/download/sha256sums/"

# Factorio related files/paths
FACTORIO_LINUX64_BIN = "factorio/bin/factorio"
FACTORIO_DATA = "factorio/data"
EXAMPLE_MAP_GEN_SETTINGS = f"{FACTORIO_DATA}/map-gen-settings.example.json"
EXAMPLE_MAP_SETTINGS = f"{FACTORIO_DATA}/map-settings.example.json"
EXAMPLE_SERVER_SETTINGS = f"{FACTORIO_DATA}/server-settings.example.json"
EXAMPLE_SERVER_WHITELIST = f"{FACTORIO_DATA}/server-whitelist.example.json"

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

# Port limits.
UPPER_PORT_LIMIT = 65565
LOWER_PORT_LIMIT = 61616
