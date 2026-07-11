# noqa: D100

import os
import secrets
from pathlib import Path

from confkit import Config

CONFIG_FILE = Path(__file__)
PROJECT_DIR = CONFIG_FILE.parent
TOML_FILE = PROJECT_DIR / "pyproject.toml"
DEFAULT_VERSION = "stable"

# confkit will auto-select a parser based on file extension; avoid explicit set_parser
Config.set_file(PROJECT_DIR/"config.ini")

# Users may edit these Config(x) values in config.ini to customize their setup.
class AppConfig:
    """Application configuration settings."""

    REQUIRE_GAME_OWNERSHIP = Config(default=False)
    PUBLIC_IP = Config("127.0.0.1") # The IP Address where servers are reachable from.
    RCON_PORT = Config(default=27015)
    # Host interface each spawned server's RCON (TCP) port is published on.
    # Defaults to loopback so RCON — which grants arbitrary in-game/Lua console
    # access — is never exposed on a public interface. Deployments where the
    # manager reaches servers over the network (e.g. the backend runs in a
    # container) should set this to a private, non-public address such as the
    # Docker bridge gateway (e.g. 172.17.0.1) and point RCON_HOST at the same.
    RCON_BIND_HOST = Config("127.0.0.1")

    # Address the *manager* dials to reach a server's RCON. Empty means reuse the
    # server's display address (PUBLIC_IP). Set this — together with
    # RCON_BIND_HOST — to a private address (e.g. the Docker bridge gateway
    # 172.17.0.1) so RCON stays off the public internet while the containerised
    # backend can still reach it.
    RCON_HOST = Config("")

    # Which orchestrator spawns Factorio servers: "docker" or "kubernetes".
    SERVER_BACKEND = Config("docker")
    # Kubernetes namespace used by the kubernetes backend.
    K8S_NAMESPACE = Config("default")
    # Container image used for Factorio servers.
    FACTORIO_IMAGE = Config("factoriotools/factorio")

    # Kubernetes only: in-API mount path of the shared ReadWriteMany mod-cache
    # volume. Empty when unset (Docker uses MOD_STORE_DIRECTORY instead).
    MOD_SHARED_ROOT = Config(default="")

    # Timeout for RCON connections and commands, in seconds.
    TIMEOUT_RCON = Config(5)

    # Comma-separated allowlist of emails permitted to log in. When empty, any
    # Factorio account that authenticates is admitted (and a warning is logged),
    # which preserves single-operator setups. Set it to lock the manager down to
    # known operators — every admitted user gets full server-management rights.
    AUTH_ALLOWED_EMAILS = Config("")

    # Inclusive range of game ports a user may request when creating a server.
    # Requests outside this range are rejected. Defaults to the high/ephemeral
    # range documented for the host firewall (see README).
    LOWER_PORT_LIMIT = Config(default=61616)
    UPPER_PORT_LIMIT = Config(default=65535)


class HTTPConfig:
    """HTTP configuration settings."""

    timeout = Config(5)


# Headers that keep Server-Sent-Events flowing through proxies/uvicorn without
# buffering or caching. Shared by every SSE endpoint (server status/logs,
# feature-flag change signals).
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


DOCKER_CONTAINER_PREFIX = "factorio-headless"

PROJECT_DIRECTORY = PROJECT_DIR
SERVERS_DIRECTORY = PROJECT_DIR / "servers"
DOWNLOADS_DIRECTORY = PROJECT_DIR / "downloads"
SAVES_DIRECTORY = PROJECT_DIR / "saves"

# Shared, deduplicated mod store (Docker/host). Each mod+version zip is downloaded
# once here and hardlinked into every server that uses it. Mod zips are immutable,
# so the bytes are safe to share. The Kubernetes equivalent lives under the shared
# volume at AppConfig.MOD_SHARED_ROOT.
MOD_STORE_DIRECTORY = SERVERS_DIRECTORY / ".mod-store"

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
# Factorio web authentication API version. Current value is 6; with
# api_version >= 2 the login response is a JSON object ({token, username}).
API_VERSION = 6

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
