from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class BackendEventPublisher:
    """
    Small synchronous bridge used by the SUMO/TraCI process.

    Sends:
        {"type": "...", "data": {...}}

    to:
        POST http://127.0.0.1:8000/events
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 1.5,
        enabled: bool = True,
    ):
        self.endpoint = base_url.rstrip("/") + "/events"
        self.timeout = timeout
        self.enabled = enabled
        self._warned = False

    def publish(self, event_type: str, data: dict[str, Any]) -> bool:
        if not self.enabled:
            return False

        payload = json.dumps(
            {
                "type": event_type,
                "data": data,
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                response.read()

            self._warned = False
            return True

        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            if not self._warned:
                print(
                    f"[BACKEND WARN] Could not publish to "
                    f"{self.endpoint}: {exc}"
                )
                self._warned = True

            return False
