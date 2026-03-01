from __future__ import annotations

from src.core.event_queue import EventPayload
from src.tools.container_client import ContainerClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


def handle_create(event: EventPayload, container_client: ContainerClient) -> None:
    logger.info("handle_create called for tool_id=%s", event.tool_id)
    # TODO: Container 생성 로직 구현

