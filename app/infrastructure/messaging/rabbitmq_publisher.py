import json
import aio_pika
from app.config import settings


class RabbitMQPublisher:
    def __init__(self):
        self._connection =None
        self.channel = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self._connection.channel()

    async def publish(self, queue_name: str, message: dict):
        if self.channel is None:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=True)
        body = json.dumps(message).encode()
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=queue.name,
        )

    async def close(self):
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    def __del__(self):
        self.close()