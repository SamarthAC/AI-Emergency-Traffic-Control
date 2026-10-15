from __future__ import annotations

import json
import queue
import threading
import time
import urllib.error
import urllib.request
from typing import Any


class BackendEventPublisher:
    """
    Non-blocking SUMO/TraCI -> FastAPI event bridge.

    Design:
    - IMPORTANT events are queued reliably in FIFO order.
    - VEHICLE_UPDATE is coalesced: only the newest unsent update is kept.
    - The simulation thread never waits for HTTP.
    - A slow backend cannot create a huge backlog of stale vehicle positions.
    """

    HIGH_FREQUENCY_TYPES = {"VEHICLE_UPDATE"}

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 0.75,
        enabled: bool = True,
    ):
        self.endpoint = base_url.rstrip("/") + "/events"
        self.timeout = timeout
        self.enabled = enabled

        # Important events are few and must not be discarded.
        self._important_queue: queue.Queue[dict[str, Any]] = queue.Queue()

        # Only the newest unsent high-frequency event is retained.
        self._latest_vehicle_event: dict[str, Any] | None = None
        self._vehicle_lock = threading.Lock()

        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._warned = False
        self._coalesced_vehicle_updates = 0

        self._worker = threading.Thread(
            target=self._run_worker,
            name="backend-event-publisher",
            daemon=True,
        )

        if self.enabled:
            self._worker.start()

    def publish(self, event_type: str, data: dict[str, Any]) -> bool:
        """
        Queue an event and return immediately.

        Important events are never intentionally dropped.
        VEHICLE_UPDATE events are coalesced so stale positions do not build up.
        """
        if not self.enabled or self._stop_event.is_set():
            return False

        event = {
            "type": event_type,
            "data": data,
        }

        if event_type in self.HIGH_FREQUENCY_TYPES:
            with self._vehicle_lock:
                if self._latest_vehicle_event is not None:
                    self._coalesced_vehicle_updates += 1
                self._latest_vehicle_event = event

            self._wake_event.set()
            return True

        self._important_queue.put_nowait(event)
        self._wake_event.set()
        return True

    def _take_latest_vehicle_event(self) -> dict[str, Any] | None:
        with self._vehicle_lock:
            event = self._latest_vehicle_event
            self._latest_vehicle_event = None
            return event

    def _has_pending_vehicle_event(self) -> bool:
        with self._vehicle_lock:
            return self._latest_vehicle_event is not None

    def _run_worker(self) -> None:
        while True:
            # Priority 1: preserve low-frequency/important state events.
            try:
                event = self._important_queue.get_nowait()
            except queue.Empty:
                event = None

            if event is not None:
                try:
                    self._send(event)
                finally:
                    self._important_queue.task_done()
                continue

            # Priority 2: send only the newest ambulance movement sample.
            vehicle_event = self._take_latest_vehicle_event()
            if vehicle_event is not None:
                self._send(vehicle_event)
                continue

            if (
                self._stop_event.is_set()
                and self._important_queue.unfinished_tasks == 0
                and not self._has_pending_vehicle_event()
            ):
                break

            self._wake_event.wait(timeout=0.1)
            self._wake_event.clear()

    def _send(self, event: dict[str, Any]) -> bool:
        payload = json.dumps(event).encode("utf-8")

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

            if self._warned:
                print("[BACKEND] Connection restored.")

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

    def flush(self, timeout: float = 3.0) -> bool:
        """
        Wait briefly for pending important events and the latest vehicle sample.
        """
        if not self.enabled:
            return True

        deadline = time.monotonic() + timeout
        self._wake_event.set()

        while time.monotonic() < deadline:
            if (
                self._important_queue.unfinished_tasks == 0
                and not self._has_pending_vehicle_event()
            ):
                return True
            time.sleep(0.02)

        return (
            self._important_queue.unfinished_tasks == 0
            and not self._has_pending_vehicle_event()
        )

    def close(self, flush_timeout: float = 3.0) -> None:
        """
        Flush pending state briefly, then stop the background worker.
        Safe to call more than once.
        """
        if not self.enabled:
            return

        self.flush(flush_timeout)
        self._stop_event.set()
        self._wake_event.set()

        if self._worker.is_alive():
            self._worker.join(timeout=1.5)

        if self._coalesced_vehicle_updates:
            print(
                "[BACKEND] Coalesced "
                f"{self._coalesced_vehicle_updates} stale VEHICLE_UPDATE "
                "event(s) while keeping the newest position."
            )

    def __enter__(self) -> "BackendEventPublisher":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
