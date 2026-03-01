from __future__ import annotations

from typing import Any

from kubernetes import client, config as k8s_config

from src.core.config import KubernetesSettings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KubernetesClient:
    """
    Kubernetes 연동 스켈레톤.
    Pod/Deployment 생성/삭제/상태 조회를 위한 최소 인터페이스만 정의한다.
    """

    def __init__(self, settings: KubernetesSettings) -> None:
        self.settings = settings
        if settings.inCluster:
            k8s_config.load_incluster_config()
        else:
            k8s_config.load_kube_config(config_file=settings.kubeconfigPath)
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()

    def create_tool_pod(self, tool: Any, resources: dict[str, Any]) -> str:
        # TODO: AnalysisTool/ResourceSpec 를 기반으로 Pod/Deployment 생성
        logger.info("create_tool_pod called for tool=%s", getattr(tool, "id", None))
        return ""

    def delete_tool_pod(self, container_id: str) -> None:
        logger.info("delete_tool_pod called for container_id=%s", container_id)

    def get_tool_status(self, container_id: str) -> dict[str, Any]:
        logger.info("get_tool_status called for container_id=%s", container_id)
        return {"containerId": container_id, "status": "UNKNOWN"}

