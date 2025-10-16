import json
import pika
from app.config import settings


class RabbitMQPublisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()

    def publish(self, queue_name: str, message: dict):
        self.channel.queue_declare(queue=queue_name, durable=True)
        body = json.dumps(message)
        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def __del__(self):
        self.connection.close()
