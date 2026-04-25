import json

import pytest

from app.infrastructure.services.broker.bobber_publisher import BobberPublisher


class _HealthyBobberClient:
    def __init__(self, *_args, **_kwargs):
        self.produce_calls = []
        self.closed = False

    def healthcheck(self):
        return True

    def produce(self, queue, key, value):
        self.produce_calls.append((queue, key, value))
        return True

    def close(self):
        self.closed = True


def test_bobber_publisher_init_raises_when_broker_unavailable(monkeypatch):
    class _UnhealthyBobberClient(_HealthyBobberClient):
        def healthcheck(self):
            return False

    monkeypatch.setattr(
        "app.infrastructure.services.broker.bobber_publisher.BobberClient",
        _UnhealthyBobberClient,
    )

    with pytest.raises(ConnectionError):
        BobberPublisher()


def test_publish_methods_build_expected_keys_and_payloads(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.services.broker.bobber_publisher.BobberClient",
        _HealthyBobberClient,
    )

    publisher = BobberPublisher()

    inference_message = {"task_id": "11", "foo": "bar"}
    training_message = {"task_id": "22", "foo": "baz"}

    assert publisher.publish_inference("inf-q", inference_message) is True
    assert publisher.publish_training("train-q", training_message) is True

    assert publisher.client.produce_calls[0][0] == "inf-q"
    assert publisher.client.produce_calls[0][1] == "inference_11"
    assert json.loads(publisher.client.produce_calls[0][2]) == inference_message

    assert publisher.client.produce_calls[1][0] == "train-q"
    assert publisher.client.produce_calls[1][1] == "training_22"
    assert json.loads(publisher.client.produce_calls[1][2]) == training_message


def test_close_delegates_to_client(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.services.broker.bobber_publisher.BobberClient",
        _HealthyBobberClient,
    )

    publisher = BobberPublisher()
    publisher.close()

    assert publisher.client.closed is True
