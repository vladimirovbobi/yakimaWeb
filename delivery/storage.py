"""R2 storage client + signed URL generator.

In dev with no AWS_S3_ENDPOINT_URL set, falls back to local filesystem at
`/app/dev_uploads/`. Production wires R2 via the standard S3-compatible API.
"""
from __future__ import annotations

import os
import pathlib
import uuid
from dataclasses import dataclass

import boto3
from botocore.client import Config

from config import get_settings


@dataclass
class StoredObject:
    key: str
    size: int


class StorageBackend:
    """Tiny abstraction so dev runs without R2 credentials."""

    def __init__(self) -> None:
        s = get_settings()
        self._bucket = s.aws_storage_bucket_name
        self._endpoint = s.aws_s3_endpoint_url
        self._has_r2 = bool(s.aws_access_key_id and s.aws_s3_endpoint_url)
        if self._has_r2:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=s.aws_access_key_id,
                aws_secret_access_key=s.aws_secret_access_key,
                region_name=s.aws_s3_region,
                config=Config(signature_version="s3v4"),
            )
        else:
            self._dev_root = pathlib.Path("/app/dev_uploads")
            self._dev_root.mkdir(parents=True, exist_ok=True)

    def make_key(self, package_id: int, filename: str) -> str:
        return f"packages/{package_id}/{uuid.uuid4().hex}-{filename}"

    def put(self, key: str, body: bytes, content_type: str) -> StoredObject:
        if self._has_r2:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
        else:
            target = self._dev_root / key
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        return StoredObject(key=key, size=len(body))

    def signed_url(self, key: str, ttl_seconds: int) -> str:
        if self._has_r2:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=ttl_seconds,
            )
        # Dev fallback: serve via the delivery service itself; safe because
        # this only runs locally with no real keys.
        return f"/api/delivery/v1/dev-files/{key}"

    def delete(self, key: str) -> None:
        if self._has_r2:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        else:
            target = self._dev_root / key
            if target.exists():
                os.remove(target)


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _backend
    if _backend is None:
        _backend = StorageBackend()
    return _backend
