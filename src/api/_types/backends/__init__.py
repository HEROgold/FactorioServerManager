"""Server orchestration backends (Docker / Kubernetes).

Use :func:`get_backend` to obtain the configured backend. The concrete
implementation modules are imported lazily so that importing this package does
not require the Docker daemon or the Kubernetes client unless that backend is
actually selected.
"""

from __future__ import annotations

from functools import cache

from api._types.backends.base import ServerBackend, ServerSpec
from api._types.enums import BackendKind
from api.constants import AppConfig

__all__ = ["BackendKind", "ServerBackend", "ServerSpec", "get_backend"]


@cache
def get_backend() -> ServerBackend:
    """Return the configured server backend (cached per process)."""
    kind = BackendKind(AppConfig.SERVER_BACKEND.lower())
    if kind is BackendKind.KUBERNETES:
        from api._types.backends.kubernetes_backend import K8sBackend  # noqa: PLC0415

        return K8sBackend()
    from api._types.backends.docker_backend import DockerBackend  # noqa: PLC0415

    return DockerBackend()
