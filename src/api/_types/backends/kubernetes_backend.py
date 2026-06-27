"""Kubernetes implementation of :class:`ServerBackend`.

Each Factorio server maps to a Deployment (one replica), a Service exposing the
game (UDP) and RCON (TCP) ports, and a PersistentVolumeClaim for ``/factorio``.
Starting/stopping scales the Deployment between 1 and 0 replicas.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException

from api._types.backends import ServerBackend
from api._types.enums import DockerStates
from api.constants import AppConfig

if TYPE_CHECKING:
    from api._types.backends.base import ServerSpec

GAME_CONTAINER_PORT = 34197
RCON_CONTAINER_PORT = 27015
_NOT_FOUND = 404


class K8sBackend(ServerBackend):
    """Spawn Factorio servers as Kubernetes Deployments."""

    def __init__(self) -> None:
        self._loaded = False
        self._namespace: str = AppConfig.K8S_NAMESPACE

    # -- configuration -------------------------------------------------
    def _load(self) -> None:
        if self._loaded:
            return
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()
        self._loaded = True

    @property
    def _apps(self) -> client.AppsV1Api:
        self._load()
        return client.AppsV1Api()

    @property
    def _core(self) -> client.CoreV1Api:
        self._load()
        return client.CoreV1Api()

    # -- manifest builders ---------------------------------------------
    @staticmethod
    def _labels(spec: ServerSpec) -> dict[str, str]:
        return {"app.kubernetes.io/name": "factorio", "fsm/server": spec.identifier}

    def _pvc(self, spec: ServerSpec) -> client.V1PersistentVolumeClaim:
        return client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name=f"{spec.identifier}-data", labels=self._labels(spec)),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                resources=client.V1ResourceRequirements(requests={"storage": "10Gi"}),
            ),
        )

    def _deployment(self, spec: ServerSpec) -> client.V1Deployment:
        labels = self._labels(spec)
        container = client.V1Container(
            name="factorio",
            image=f"{AppConfig.FACTORIO_IMAGE}:{spec.version}",
            ports=[
                client.V1ContainerPort(container_port=GAME_CONTAINER_PORT, protocol="UDP"),
                client.V1ContainerPort(container_port=RCON_CONTAINER_PORT, protocol="TCP"),
            ],
            volume_mounts=[client.V1VolumeMount(name="data", mount_path="/factorio")],
        )
        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=[
                client.V1Volume(
                    name="data",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=f"{spec.identifier}-data",
                    ),
                ),
            ],
        )
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(name=spec.identifier, labels=labels),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels=labels),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=pod_spec,
                ),
            ),
        )

    def _service(self, spec: ServerSpec) -> client.V1Service:
        return client.V1Service(
            metadata=client.V1ObjectMeta(name=spec.identifier, labels=self._labels(spec)),
            spec=client.V1ServiceSpec(
                type="LoadBalancer",
                selector=self._labels(spec),
                ports=[
                    client.V1ServicePort(name="game", protocol="UDP", port=spec.game_port, target_port=GAME_CONTAINER_PORT),
                    client.V1ServicePort(name="rcon", protocol="TCP", port=spec.rcon_port, target_port=RCON_CONTAINER_PORT),
                ],
            ),
        )

    # -- ServerBackend protocol ----------------------------------------
    async def create(self, spec: ServerSpec) -> None:
        def _create() -> None:
            ns = self._namespace
            self._core.create_namespaced_persistent_volume_claim(ns, self._pvc(spec))
            self._apps.create_namespaced_deployment(ns, self._deployment(spec))
            self._core.create_namespaced_service(ns, self._service(spec))

        await asyncio.to_thread(_create)

    async def start(self, spec: ServerSpec) -> None:
        await asyncio.to_thread(self._scale, spec.identifier, 1)

    async def stop(self, spec: ServerSpec) -> None:
        await asyncio.to_thread(self._scale, spec.identifier, 0)

    async def restart(self, spec: ServerSpec) -> None:
        def _restart() -> None:
            stamp = datetime.now(tz=UTC).isoformat()
            patch = {
                "spec": {
                    "template": {
                        "metadata": {"annotations": {"fsm/restartedAt": stamp}},
                    },
                },
            }
            self._apps.patch_namespaced_deployment(spec.identifier, self._namespace, patch)

        await asyncio.to_thread(_restart)

    async def remove(self, spec: ServerSpec) -> None:
        def _remove() -> None:
            ns = self._namespace
            for delete in (
                lambda: self._apps.delete_namespaced_deployment(spec.identifier, ns),
                lambda: self._core.delete_namespaced_service(spec.identifier, ns),
                lambda: self._core.delete_namespaced_persistent_volume_claim(f"{spec.identifier}-data", ns),
            ):
                try:
                    delete()
                except ApiException as exc:
                    if exc.status != _NOT_FOUND:
                        raise

        await asyncio.to_thread(_remove)

    def _scale(self, identifier: str, replicas: int) -> None:
        self._apps.patch_namespaced_deployment_scale(
            identifier,
            self._namespace,
            {"spec": {"replicas": replicas}},
        )

    def status(self, spec: ServerSpec) -> str:
        try:
            result = self._apps.read_namespaced_deployment(spec.identifier, self._namespace)
        except ApiException as exc:
            if exc.status == _NOT_FOUND:
                return DockerStates.UNKNOWN.value
            raise
        deployment = cast("client.V1Deployment", result)
        desired = (deployment.spec.replicas if deployment.spec else 0) or 0
        status = deployment.status
        available = (status.available_replicas if status else 0) or 0
        if desired == 0:
            return DockerStates.EXITED.value
        if available >= desired:
            return DockerStates.RUNNING.value
        return DockerStates.RESTARTING.value
