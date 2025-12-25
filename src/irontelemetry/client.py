"""Main IronTelemetry client class."""

import platform
import random
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .breadcrumbs import BreadcrumbManager
from .config import generate_event_id, resolve_options
from .journey import Journey, JourneyScope, Step
from .queue import OfflineQueue
from .transport import Transport
from .types import (
    Breadcrumb,
    BreadcrumbCategory,
    ExceptionInfo,
    PlatformInfo,
    SendResult,
    SeverityLevel,
    StackFrame,
    TelemetryEvent,
    TelemetryOptions,
    User,
)


class TelemetryClient:
    """Main IronTelemetry client class."""

    def __init__(self, options: TelemetryOptions):
        self._options, self._parsed_dsn = resolve_options(options)
        self._transport = Transport(
            self._parsed_dsn,
            self._options.api_base_url or self._parsed_dsn.api_base_url,
            self._options.debug,
        )
        self._queue: Optional[OfflineQueue] = None
        if self._options.enable_offline_queue:
            self._queue = OfflineQueue(
                self._options.max_offline_queue_size,
                self._options.debug,
            )
        self._breadcrumbs = BreadcrumbManager(self._options.max_breadcrumbs)

        self._tags: Dict[str, str] = {}
        self._extra: Dict[str, Any] = {}
        self._user: Optional[User] = None
        self._current_journey: Optional[Journey] = None

        if self._options.debug:
            print(f"[IronTelemetry] Initialized with DSN: {self._options.dsn}")

    def capture_exception(
        self,
        error: BaseException,
        extra: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Capture an exception."""
        exception = self._parse_exception(error)
        event = self._create_event(SeverityLevel.ERROR, exception.message, exception)

        if extra:
            event.extra.update(extra)

        return self._send_event(event)

    async def capture_exception_async(
        self,
        error: BaseException,
        extra: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Capture an exception asynchronously."""
        exception = self._parse_exception(error)
        event = self._create_event(SeverityLevel.ERROR, exception.message, exception)

        if extra:
            event.extra.update(extra)

        return await self._send_event_async(event)

    def capture_message(
        self,
        message: str,
        level: SeverityLevel = SeverityLevel.INFO,
    ) -> SendResult:
        """Capture a message."""
        event = self._create_event(level, message)
        return self._send_event(event)

    async def capture_message_async(
        self,
        message: str,
        level: SeverityLevel = SeverityLevel.INFO,
    ) -> SendResult:
        """Capture a message asynchronously."""
        event = self._create_event(level, message)
        return await self._send_event_async(event)

    def add_breadcrumb(
        self,
        message: str,
        category: BreadcrumbCategory = BreadcrumbCategory.CUSTOM,
        level: SeverityLevel = SeverityLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a breadcrumb."""
        self._breadcrumbs.add(message, category, level, data)

    def set_user(
        self,
        id: str,
        email: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set user context."""
        self._user = User(id=id, email=email, data=data)

    def clear_user(self) -> None:
        """Clear user context."""
        self._user = None

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag."""
        self._tags[key] = value

    def set_extra(self, key: str, value: Any) -> None:
        """Set extra context."""
        self._extra[key] = value

    def start_journey(self, name: str) -> JourneyScope:
        """Start a new journey."""
        self._current_journey = Journey(name)

        # Copy user context to journey
        if self._user:
            self._current_journey.set_user(
                self._user.id,
                self._user.email,
                self._user.data,
            )

        def on_complete() -> None:
            self._current_journey = None

        return JourneyScope(self._current_journey, on_complete)

    def start_step(self, name: str, category: Optional[str] = None) -> Step:
        """Start a step in the current journey."""
        if not self._current_journey:
            raise RuntimeError("No active journey. Call start_journey() first.")

        return self._current_journey.start_step(name, category)

    def flush(self) -> None:
        """Flush pending events."""
        self._process_queue()

    async def flush_async(self) -> None:
        """Flush pending events asynchronously."""
        await self._process_queue_async()

    def close(self) -> None:
        """Close the client."""
        self._transport.close()

    def _create_event(
        self,
        level: SeverityLevel,
        message: Optional[str] = None,
        exception: Optional[ExceptionInfo] = None,
    ) -> TelemetryEvent:
        """Create a telemetry event."""
        user = self._current_journey.get_user() if self._current_journey else self._user

        return TelemetryEvent(
            event_id=generate_event_id(),
            timestamp=datetime.now(),
            level=level,
            message=message,
            exception=exception,
            user=user,
            tags=dict(self._tags),
            extra=dict(self._extra),
            breadcrumbs=self._breadcrumbs.get_all(),
            journey=self._current_journey.get_context() if self._current_journey else None,
            environment=self._options.environment,
            app_version=self._options.app_version,
            platform=self._get_platform_info(),
        )

    def _send_event(self, event: TelemetryEvent) -> SendResult:
        """Send an event."""
        # Check sample rate
        if random.random() > self._options.sample_rate:
            if self._options.debug:
                print("[IronTelemetry] Event dropped due to sample rate")
            return SendResult(success=True, event_id=event.event_id)

        # Apply before_send hook
        if self._options.before_send:
            result = self._options.before_send(event)
            if result is None:
                if self._options.debug:
                    print("[IronTelemetry] Event dropped by before_send hook")
                return SendResult(success=True, event_id=event.event_id)
            event = result

        # Try to send
        result = self._transport.send(event)

        if not result.success and self._queue:
            self._queue.enqueue(event)
            return SendResult(
                success=result.success,
                event_id=event.event_id,
                error=result.error,
                queued=True,
            )

        return result

    async def _send_event_async(self, event: TelemetryEvent) -> SendResult:
        """Send an event asynchronously."""
        # Check sample rate
        if random.random() > self._options.sample_rate:
            if self._options.debug:
                print("[IronTelemetry] Event dropped due to sample rate")
            return SendResult(success=True, event_id=event.event_id)

        # Apply before_send hook
        if self._options.before_send:
            result = self._options.before_send(event)
            if result is None:
                if self._options.debug:
                    print("[IronTelemetry] Event dropped by before_send hook")
                return SendResult(success=True, event_id=event.event_id)
            event = result

        # Try to send
        result = await self._transport.send_async(event)

        if not result.success and self._queue:
            self._queue.enqueue(event)
            return SendResult(
                success=result.success,
                event_id=event.event_id,
                error=result.error,
                queued=True,
            )

        return result

    def _process_queue(self) -> None:
        """Process offline queue."""
        if not self._queue or self._queue.is_empty:
            return

        if not self._transport.is_online():
            return

        for event in self._queue.get_all():
            result = self._transport.send(event)
            if result.success:
                self._queue.remove(event.event_id)

    async def _process_queue_async(self) -> None:
        """Process offline queue asynchronously."""
        if not self._queue or self._queue.is_empty:
            return

        if not self._transport.is_online():
            return

        for event in self._queue.get_all():
            result = await self._transport.send_async(event)
            if result.success:
                self._queue.remove(event.event_id)

    def _parse_exception(self, error: BaseException) -> ExceptionInfo:
        """Parse an error into exception info."""
        tb = error.__traceback__
        frames: List[StackFrame] = []

        if tb:
            for frame_summary in traceback.extract_tb(tb):
                frames.append(
                    StackFrame(
                        function=frame_summary.name,
                        filename=frame_summary.filename,
                        lineno=frame_summary.lineno,
                    )
                )

        return ExceptionInfo(
            type=type(error).__name__,
            message=str(error),
            stacktrace=frames if frames else None,
        )

    def _get_platform_info(self) -> PlatformInfo:
        """Get platform information."""
        return PlatformInfo(
            name="python",
            version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            os=platform.system(),
        )
