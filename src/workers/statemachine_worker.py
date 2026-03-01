from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from src.core.event_queue import EventPayload, EventQueue, get_event_queue
from src.utils.logging import configure_root_logger, get_logger

logger = get_logger(__name__)


def handle_event(event: EventPayload) -> None:
    # TODO: event_type 에 따라 actions 모듈의 핸들러로 위임
    logger.info("Handling event type=%s tool_id=%s", event.event_type, event.tool_id)


def main() -> None:
    configure_root_logger()
    logger.info("StateMachine worker started")

    queue: EventQueue = get_event_queue()
    executor = ThreadPoolExecutor(max_workers=4)

    def dispatch(event: EventPayload) -> None:
        executor.submit(handle_event, event)

    queue.consume(dispatch)

    # 간단한 무한 루프 유지
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

