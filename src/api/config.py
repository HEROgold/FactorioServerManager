""""Configuration for the fsm API."""
from functools import cache
from pathlib import Path
from typing import Any

from confkit import Config as BaseConfig
from confkit.parsers import EnvParser
from pydantic import BaseModel, create_model


class Config[T](BaseConfig[T]):
    """Namespaced configuration for the fsm API."""

Config.set_file(Path("api_config.ini"))


# --- Secrets from the environment / .env (via confkit) -----------------------
# Secrets (Sentry DSN, the flag-change signing secret) must not live in the
# git-tracked ini. confkit's EnvParser reads os.environ *plus* an optional .env
# (env wins, quotes/comments handled). It is read-only, so we use it directly
# rather than as a Config descriptor: a missing key would otherwise make confkit
# try to persist the default and raise NotImplementedError at import.
_env_parser = EnvParser()
_env_parser.read(Path(".env"))


def env_value(key: str, fallback: str = "") -> str:
    """Read a secret from the environment / .env via confkit. Section is ignored."""
    return (_env_parser.get("", key, fallback=fallback) or "").strip().strip('"')


# Sentry generic feature-flag change-tracking webhook. When either is unset the
# backend simply doesn't emit change events (see api.sentry_flags).
SENTRY_FLAGS_WEBHOOK_URL = env_value("SENTRY_FLAGS_WEBHOOK_URL")
SENTRY_FLAGS_SIGNING_SECRET = env_value("SENTRY_FLAGS_SIGNING_SECRET")

class AppConfig:
    """Application configuration."""

    host = Config("host")
    port = Config(8000)
    sentry_dsn = Config("sentry_dsn")
    reload = Config(default=False)
    environment = Config("production")

class SessionConfig:
    """Security-related configuration."""

    secret = Config("secret")
    algorithm = Config("HS256")
    cookie_name = Config("fsm_session")

app_config = AppConfig()
session_config = SessionConfig()


# --- Feature flags -----------------------------------------------------------
# One source of truth: the `FeatureFlags` class below. Flag names, defaults and
# ini bootstrapping all come from it; the payload dict, the Pydantic response
# model and the live re-read are derived by walking it (no duplicated shape).

type FlagTree = dict[str, "bool | FlagTree"]  # recursive: bool leaves or nested groups


class FeatureFlags:
    """THE single source of truth for feature flags.

    Add a flag = one line; add a nested group = one nested class. confkit builds
    each ini section from the owner's __qualname__, so the nested `Mods` class
    lives under [FeatureFlags.Mods]. Sections/defaults are auto-written to
    api_config.ini on first import; toggle them per-environment there.
    """

    rcon_console = Config(default=True)      # existing RCON tab
    server_create = Config(default=True)     # existing server-creation flow

    class Mods:                      # -> section [FeatureFlags.Mods]
        """Feature flags for the Mods tab and sub-tabs."""

        enabled = Config(default=False)      # dark-launch: the whole Mods tab
        manage = Config(default=True)        # "Installed" sub-tab
        download = Config(default=True)      # "Download" (mod-portal search) sub-tab


def collect_flags(namespace: type) -> FlagTree:
    """Read current flag values into a nested dict (Config -> bool, nested class -> group)."""
    out: FlagTree = {}
    for name, attr in vars(namespace).items():
        if isinstance(attr, Config):
            out[name] = bool(getattr(namespace, name))
        elif isinstance(attr, type) and not name.startswith("_"):
            out[name] = collect_flags(attr)
    return out


@cache
def flags_model(namespace: type = FeatureFlags, name: str = "FeatureFlagsModel") -> type[BaseModel]:
    """Generate the Pydantic response model from the SAME class (no duplicated shape)."""
    fields: dict[str, Any] = {}
    for attr_name, attr in vars(namespace).items():
        if isinstance(attr, Config):
            fields[attr_name] = (bool, ...)
        elif isinstance(attr, type) and not attr_name.startswith("_"):
            fields[attr_name] = (flags_model(attr, attr_name), ...)
    return create_model(name, **fields)


FeatureFlagsModel = flags_model()


def read_flags() -> FlagTree:
    """Re-read the ini so mid-run edits are reflected (confkit caches the parser), then collect."""
    Config._parser.read(Config._file)  # noqa: SLF001 - our Config subclass owns the shared parser/file
    return collect_flags(FeatureFlags)
