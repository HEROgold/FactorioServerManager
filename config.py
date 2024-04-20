# noqa: D100

from pathlib import Path
from tomllib import loads


toml = loads("pyproject.toml")

PROJECT_NAME = toml["project"]["name"]
PROJECT_VERSION = toml["project"]["version"]
SERVERS_DIRECTORY = Path(__file__).parent / "servers"

MODS_API_URL = "https://mods.factorio.com/api/mods"
LOGIN_URL = "https://www.factorio.com/login"
RELEASES_URL = "https://factorio.com/api/latest-releases"
ARCHIVE_URL = "https://www.factorio.com/download/archive"
AVAILABLE_UPDATES_URL = "https://updater.factorio.com/get-available-versions."

