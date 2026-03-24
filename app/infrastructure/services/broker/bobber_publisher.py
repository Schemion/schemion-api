from bobber import BobberClient
from typing import Dict, Any


class BobberPublisher:
    def __init__(self, host: str = 'localhost', port: int = 50051):
        self.client = BobberClient(host, port)
        if not self.client.healthcheck():
            raise ConnectionError("Bobber broker unavailable")

    def publish_inference(self, queue: str, message: dict):
        key = f"inference_{message.get('task_id', 'unknown')}"
        value = json.dumps(message)
        success = self.client.produce(queue, key, value)
        return success

    def publish_training(self, queue: str, message: dict):
        key = f"training_{message.get('task_id', 'unknown')}"
        value = json.dumps(message)
        success = self.client.produce(queue, key, value)
        return success

    def close(self):
        self.client.close()
