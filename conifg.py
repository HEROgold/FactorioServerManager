# noqa: D100

from tomllib import loads


toml = loads("pyproject.toml")

PROJECT_NAME = toml["project"]["name"]
PROJECT_VERSION = toml["project"]["version"]
