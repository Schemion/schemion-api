from app.infrastructure.services.cloud_storage.minio_storage import MinioStorage
from tests.utils import run


class _FakeMinio:
    def __init__(self, *args, **kwargs):
        self.buckets = set()
        self.put_calls = []
        self.remove_calls = []
        self.presigned_calls = []
        self.exists_calls = []
        self.make_calls = []

    async def bucket_exists(self, bucket):
        self.exists_calls.append(bucket)
        return bucket in self.buckets

    async def make_bucket(self, bucket):
        self.make_calls.append(bucket)
        self.buckets.add(bucket)

    async def put_object(self, bucket_name, object_name, data, length, content_type):
        self.put_calls.append((bucket_name, object_name, length, content_type))

    async def remove_object(self, bucket_name, object_name):
        self.remove_calls.append((bucket_name, object_name))

    async def presigned_get_object(self, bucket_name, object_name, expires):
        self.presigned_calls.append((bucket_name, object_name, expires))
        return "url"


def test_upload_file_creates_bucket_and_uploads(monkeypatch):
    monkeypatch.setattr("app.infrastructure.services.cloud_storage.minio_storage.Minio", _FakeMinio)
    monkeypatch.setattr("app.infrastructure.services.cloud_storage.minio_storage.uuid.uuid4", lambda: "fixed")

    storage = MinioStorage("endpoint", "key", "secret")
    result = run(storage.upload_file(b"data", "file.bin", "application/octet-stream", "bucket"))

    assert result == "fixed_file.bin"
    assert "bucket" in storage.client.make_calls
    assert storage.client.put_calls[0][0] == "bucket"


def test_delete_and_presign(monkeypatch):
    monkeypatch.setattr("app.infrastructure.services.cloud_storage.minio_storage.Minio", _FakeMinio)

    storage = MinioStorage("endpoint", "key", "secret")
    run(storage.delete_file("obj", "bucket"))
    url = run(storage.get_presigned_file_url("obj", "bucket", expires=10))

    assert storage.client.remove_calls == [("bucket", "obj")]
    assert url == "url"
