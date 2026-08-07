"""HTTP mixin for AI provider adapters using urllib (stdlib only)."""
from __future__ import annotations

import json
import urllib.request
from typing import Any


class HTTPMixin:
    def _post_json(self, url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get_json(self, url: str, headers: dict[str, str], timeout: int = 30) -> dict[str, Any]:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
