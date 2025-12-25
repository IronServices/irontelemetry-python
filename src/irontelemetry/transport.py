"""HTTP transport for sending events to the server."""

from datetime import datetime
from typing import Any, Dict

import httpx

from .types import ParsedDsn, SendResult, TelemetryEvent


class Transport:
    """HTTP transport for sending events to the server."""

    def __init__(
        self,
        parsed_dsn: ParsedDsn,
        api_base_url: str,
        debug: bool = False,
        timeout: float = 30.0,
    ):
        self._api_base_url = api_base_url
        self._public_key = parsed_dsn.public_key
        self._debug = debug
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def send(self, event: TelemetryEvent) -> SendResult:
        """Send an event to the server."""
        url = f"{self._api_base_url}/api/v1/events"

        try:
            response = self._client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-Public-Key": self._public_key,
                },
                json=self._serialize_event(event),
            )

            if response.status_code >= 400:
                if self._debug:
                    print(f"[IronTelemetry] Failed to send event: {response.status_code}")
                return SendResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}",
                )

            result = response.json()

            if self._debug:
                print(f"[IronTelemetry] Event sent successfully: {event.event_id}")

            return SendResult(
                success=True,
                event_id=result.get("eventId", event.event_id),
            )

        except Exception as e:
            if self._debug:
                print(f"[IronTelemetry] Failed to send event: {e}")
            return SendResult(success=False, error=str(e))

    async def send_async(self, event: TelemetryEvent) -> SendResult:
        """Send an event to the server asynchronously."""
        url = f"{self._api_base_url}/api/v1/events"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "X-Public-Key": self._public_key,
                    },
                    json=self._serialize_event(event),
                )

                if response.status_code >= 400:
                    if self._debug:
                        print(f"[IronTelemetry] Failed to send event: {response.status_code}")
                    return SendResult(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()

                if self._debug:
                    print(f"[IronTelemetry] Event sent successfully: {event.event_id}")

                return SendResult(
                    success=True,
                    event_id=result.get("eventId", event.event_id),
                )

        except Exception as e:
            if self._debug:
                print(f"[IronTelemetry] Failed to send event: {e}")
            return SendResult(success=False, error=str(e))

    def is_online(self) -> bool:
        """Check if the server is reachable."""
        try:
            response = self._client.get(
                f"{self._api_base_url}/api/v1/health",
                headers={"X-Public-Key": self._public_key},
            )
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        """Close the transport."""
        self._client.close()

    def _serialize_event(self, event: TelemetryEvent) -> Dict[str, Any]:
        """Serialize an event for sending."""
        return {
            "eventId": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "level": event.level.value,
            "message": event.message,
            "exception": self._serialize_exception(event.exception) if event.exception else None,
            "user": self._serialize_user(event.user) if event.user else None,
            "tags": event.tags,
            "extra": event.extra,
            "breadcrumbs": [self._serialize_breadcrumb(b) for b in event.breadcrumbs],
            "journey": self._serialize_journey(event.journey) if event.journey else None,
            "environment": event.environment,
            "appVersion": event.app_version,
            "platform": {
                "name": event.platform.name,
                "version": event.platform.version,
                "os": event.platform.os,
            },
        }

    def _serialize_exception(self, exc: Any) -> Dict[str, Any]:
        """Serialize exception info."""
        return {
            "type": exc.type,
            "message": exc.message,
            "stacktrace": [
                {
                    "function": f.function,
                    "filename": f.filename,
                    "lineno": f.lineno,
                    "colno": f.colno,
                }
                for f in (exc.stacktrace or [])
            ] if exc.stacktrace else None,
        }

    def _serialize_user(self, user: Any) -> Dict[str, Any]:
        """Serialize user info."""
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "data": user.data,
        }

    def _serialize_breadcrumb(self, breadcrumb: Any) -> Dict[str, Any]:
        """Serialize a breadcrumb."""
        return {
            "timestamp": breadcrumb.timestamp.isoformat(),
            "category": breadcrumb.category.value,
            "message": breadcrumb.message,
            "level": breadcrumb.level.value,
            "data": breadcrumb.data,
        }

    def _serialize_journey(self, journey: Any) -> Dict[str, Any]:
        """Serialize journey context."""
        return {
            "journeyId": journey.journey_id,
            "name": journey.name,
            "currentStep": journey.current_step,
            "startedAt": journey.started_at.isoformat(),
            "metadata": journey.metadata,
        }
