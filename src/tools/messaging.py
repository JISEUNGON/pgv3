from __future__ import annotations

from typing import Any, Callable

import pika

from src.core.config import MessagingSettings


class RabbitMQClient:
    def __init__(self, settings: MessagingSettings) -> None:
        self.settings = settings
        params = pika.ConnectionParameters(
            host=settings.host,
            port=settings.port,
            virtual_host=settings.vhost,
            credentials=pika.PlainCredentials(settings.username, settings.password),
        )
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

    def ensure_queue(self, queue: str) -> None:
        self._channel.queue_declare(queue=queue, durable=True)

    def publish(self, queue: str, message: dict[str, Any]) -> None:
        self.ensure_queue(queue)
        self._channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=str(message).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def consume(self, queue: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self.ensure_queue(queue)

        def _callback(ch, method, properties, body):
            # TODO: 적절한 직렬화/역직렬화 적용 (JSON 등)
            handler({"raw": body.decode("utf-8")})
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self._channel.basic_consume(queue=queue, on_message_callback=_callback)
        self._channel.start_consuming()

