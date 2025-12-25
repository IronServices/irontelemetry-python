"""Offline queue for storing events when the network is unavailable."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .types import (
    Breadcrumb,
    BreadcrumbCategory,
    ExceptionInfo,
    JourneyContext,
    PlatformInfo,
    SeverityLevel,
    StackFrame,
    TelemetryEvent,
    User,
)


class OfflineQueue:
    """Offline queue for storing events when the network is unavailable."""

    def __init__(
        self,
        max_size: int = 500,
        debug: bool = False,
        storage_path: Optional[Path] = None,
    ):
        self._max_size = max_size
        self._debug = debug
        self._queue: List[TelemetryEvent] = []

        # Default to user's local app data directory
        if storage_path is None:
            app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
            storage_path = Path(app_data) / ".irontelemetry"

        self._storage_path = storage_path
        self._queue_file = self._storage_path / "queue.json"

        self._load()

    def enqueue(self, event: TelemetryEvent) -> None:
        """Add an event to the queue."""
        if len(self._queue) >= self._max_size:
            self._queue.pop(0)
            if self._debug:
                print("[IronTelemetry] Queue full, dropping oldest event")

        self._queue.append(event)
        self._save()

        if self._debug:
            print(f"[IronTelemetry] Event queued, queue size: {len(self._queue)}")

    def get_all(self) -> List[TelemetryEvent]:
        """Get all queued events."""
        return list(self._queue)

    def remove(self, event_id: str) -> None:
        """Remove an event from the queue."""
        self._queue = [e for e in self._queue if e.event_id != event_id]
        self._save()

    def clear(self) -> None:
        """Clear all queued events."""
        self._queue = []
        self._save()

    @property
    def size(self) -> int:
        """Get the number of queued events."""
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._queue) == 0

    def _load(self) -> None:
        """Load queue from persistent storage."""
        try:
            if self._queue_file.exists():
                with open(self._queue_file, "r") as f:
                    data = json.load(f)
                    self._queue = [self._deserialize_event(e) for e in data]
        except Exception as e:
            if self._debug:
                print(f"[IronTelemetry] Failed to load queue from storage: {e}")

    def _save(self) -> None:
        """Save queue to persistent storage."""
        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            with open(self._queue_file, "w") as f:
                json.dump([self._serialize_event(e) for e in self._queue], f)
        except Exception as e:
            if self._debug:
                print(f"[IronTelemetry] Failed to save queue to storage: {e}")

    def _serialize_event(self, event: TelemetryEvent) -> dict:
        """Serialize an event for storage."""
        return {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "level": event.level.value,
            "message": event.message,
            "exception": {
                "type": event.exception.type,
                "message": event.exception.message,
                "stacktrace": [
                    {"function": f.function, "filename": f.filename, "lineno": f.lineno}
                    for f in (event.exception.stacktrace or [])
                ] if event.exception.stacktrace else None,
            } if event.exception else None,
            "user": {
                "id": event.user.id,
                "email": event.user.email,
                "data": event.user.data,
            } if event.user else None,
            "tags": event.tags,
            "extra": event.extra,
            "breadcrumbs": [
                {
                    "timestamp": b.timestamp.isoformat(),
                    "category": b.category.value,
                    "message": b.message,
                    "level": b.level.value,
                    "data": b.data,
                }
                for b in event.breadcrumbs
            ],
            "journey": {
                "journey_id": event.journey.journey_id,
                "name": event.journey.name,
                "current_step": event.journey.current_step,
                "started_at": event.journey.started_at.isoformat(),
                "metadata": event.journey.metadata,
            } if event.journey else None,
            "environment": event.environment,
            "app_version": event.app_version,
            "platform": {
                "name": event.platform.name,
                "version": event.platform.version,
                "os": event.platform.os,
            },
        }

    def _deserialize_event(self, data: dict) -> TelemetryEvent:
        """Deserialize an event from storage."""
        exception = None
        if data.get("exception"):
            exc_data = data["exception"]
            stacktrace = None
            if exc_data.get("stacktrace"):
                stacktrace = [
                    StackFrame(
                        function=f.get("function"),
                        filename=f.get("filename"),
                        lineno=f.get("lineno"),
                    )
                    for f in exc_data["stacktrace"]
                ]
            exception = ExceptionInfo(
                type=exc_data["type"],
                message=exc_data["message"],
                stacktrace=stacktrace,
            )

        user = None
        if data.get("user"):
            user_data = data["user"]
            user = User(
                id=user_data["id"],
                email=user_data.get("email"),
                data=user_data.get("data"),
            )

        journey = None
        if data.get("journey"):
            j_data = data["journey"]
            journey = JourneyContext(
                journey_id=j_data["journey_id"],
                name=j_data["name"],
                current_step=j_data.get("current_step"),
                started_at=datetime.fromisoformat(j_data["started_at"]),
                metadata=j_data.get("metadata", {}),
            )

        breadcrumbs = [
            Breadcrumb(
                timestamp=datetime.fromisoformat(b["timestamp"]),
                category=BreadcrumbCategory(b["category"]),
                message=b["message"],
                level=SeverityLevel(b["level"]),
                data=b.get("data"),
            )
            for b in data.get("breadcrumbs", [])
        ]

        platform_data = data.get("platform", {})
        platform = PlatformInfo(
            name=platform_data.get("name", "python"),
            version=platform_data.get("version"),
            os=platform_data.get("os"),
        )

        return TelemetryEvent(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=SeverityLevel(data["level"]),
            message=data.get("message"),
            exception=exception,
            user=user,
            tags=data.get("tags", {}),
            extra=data.get("extra", {}),
            breadcrumbs=breadcrumbs,
            journey=journey,
            environment=data.get("environment"),
            app_version=data.get("app_version"),
            platform=platform,
        )
