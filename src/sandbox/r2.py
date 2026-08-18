"""R2 storage backend — Cloudflare R2 for bounty artifacts and evidence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


class R2Storage:
    """Cloudflare R2 S3-compatible storage client."""

    def __init__(self, account_id: str | None = None, access_key_id: str | None = None,
                 secret_access_key: str | None = None, endpoint: str | None = None,
                 bucket: str | None = None):
        self.account_id = account_id or os.environ.get("CLOUDFLARE_R2_ACCOUNT_ID", "")
        self.access_key_id = access_key_id or os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID", "")
        self.secret_access_key = secret_access_key or os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY", "")
        self.endpoint = endpoint or os.environ.get("CLOUDFLARE_R2_ENDPOINT", "")
        self.bucket = bucket or os.environ.get("CLOUDFLARE_R2_BUCKET", "qdwsandbox")
        self._base_url = f"{self.endpoint}/{self.bucket}"

    def is_configured(self) -> bool:
        return bool(self.account_id and self.access_key_id and self.secret_access_key and self.endpoint)

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> dict[str, Any]:
        url = f"{self._base_url}/{key}"
        headers = self._sign_request("PUT", key, content_type)
        headers["Content-Type"] = content_type
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, content=data, headers=headers, timeout=30)
            resp.raise_for_status()
        return {"key": key, "size": len(data), "status": "uploaded"}

    async def download(self, key: str) -> bytes:
        url = f"{self._base_url}/{key}"
        headers = self._sign_request("GET", key)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
        return resp.content

    async def delete(self, key: str) -> dict[str, Any]:
        url = f"{self._base_url}/{key}"
        headers = self._sign_request("DELETE", key)
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=headers, timeout=30)
            resp.raise_for_status()
        return {"key": key, "status": "deleted"}

    async def head(self, key: str) -> dict[str, Any] | None:
        url = f"{self._base_url}/{key}"
        headers = self._sign_request("HEAD", key)
        async with httpx.AsyncClient() as client:
            resp = await client.head(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return {"key": key, "content_length": int(resp.headers.get("Content-Length", 0))}
            return None

    def _sign_request(self, method: str, key: str, content_type: str = "") -> dict[str, str]:
        """Placeholder for AWS Signature V4 signing."""
        return {
            "Authorization": f"Bearer {self.access_key_id}",
            "x-amz-date": __import__("datetime").datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        }


def get_r2_storage() -> R2Storage:
    return R2Storage()
