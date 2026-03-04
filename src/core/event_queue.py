from __future__ import annotations

from enum import Enum
from queue import Queue, Empty
from threading import Thread
from typing import Callable, Protocol

from pydantic import BaseModel


class EventType(str, Enum):
    CREATE = "CREATE"
    STOP = "STOP"
    DELETE = "DELETE"
    BACKUP = "BACKUP"


class EventPayload(BaseModel):
    event_type: EventType
    tool_id: str
    user_id: str | None = None
    data: dict | None = None


class EventQueue(Protocol):
    def publish(self, event: EventPayload) -> None: ...

    def consume(self, handler: Callable[[EventPayload], None]) -> None: ...


class InMemoryEventQueue:
    """
    간단한 인메모리 EventQueue 구현.
    실제 환경에서는 RabbitMQ/Redis 기반 구현으로 교체한다.
    """

    def __init__(self) -> None:
        self._queue: Queue[EventPayload] = Queue()

    def publish(self, event: EventPayload) -> None:
        self._queue.put(event)

    def consume(self, handler: Callable[[EventPayload], None]) -> None:
        def _loop() -> None:
            while True:
                try:
                    event = self._queue.get(timeout=1.0)
                except Empty:
                    continue
                handler(event)

        Thread(target=_loop, daemon=True).start()


_default_queue: InMemoryEventQueue | None = None


def get_event_queue() -> InMemoryEventQueue:
    global _default_queue
    if _default_queue is None:
        _default_queue = InMemoryEventQueue()
    return _default_queue

