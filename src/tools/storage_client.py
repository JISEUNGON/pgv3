from __future__ import annotations

from typing import BinaryIO

from minio import Minio

from src.core.config import StorageSettings


class StorageClient:
    """
    MinIO/오브젝트 스토리지 연동 스켈레톤.
    """

    def __init__(self, settings: StorageSettings) -> None:
        self.settings = settings
        self._client = Minio(
            settings.endpoint.replace("http://", "").replace("https://", ""),
            access_key=settings.accessKey,
            secret_key=settings.secretKey,
            secure=settings.endpoint.startswith("https://"),
        )

    def upload_file(self, file_obj: BinaryIO, object_name: str, content_type: str | None = None) -> str:
        self._client.put_object(
            self.settings.bucket,
            object_name,
            data=file_obj,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=content_type,
        )
        return object_name

    def download_file(self, object_name: str, target_path: str) -> None:
        self._client.fget_object(self.settings.bucket, object_name, target_path)

    def get_object_url(self, object_name: str, expire_seconds: int) -> str:
        url = self._client.presigned_get_object(self.settings.bucket, object_name, expire_seconds)
        return str(url)

