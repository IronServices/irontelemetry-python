"""IronTelemetry SDK for Python.

Error monitoring and crash reporting SDK for Python applications.
"""

import sys
from typing import Any, Callable, Dict, Optional, TypeVar

from .client import TelemetryClient
from .journey import Journey, JourneyScope, Step
from .types import (
    Breadcrumb,
    BreadcrumbCategory,
    ExceptionInfo,
    JourneyContext,
    ParsedDsn,
    PlatformInfo,
    SendResult,
    SeverityLevel,
    StackFrame,
    TelemetryEvent,
    TelemetryOptions,
    User,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "TelemetryClient",
    "TelemetryOptions",
    # Types
    "Breadcrumb",
    "BreadcrumbCategory",
    "ExceptionInfo",
    "JourneyContext",
    "ParsedDsn",
    "PlatformInfo",
    "SendResult",
    "SeverityLevel",
    "StackFrame",
    "TelemetryEvent",
    "User",
    # Journey
    "Journey",
    "JourneyScope",
    "Step",
    # Functions
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "set_user",
    "clear_user",
    "set_tag",
    "set_extra",
    "start_journey",
    "start_step",
    "flush",
    "close",
    "use_unhandled_exception_handler",
    "track_step",
]

# Global client instance
_client: Optional[TelemetryClient] = None

T = TypeVar("T")


def init(dsn_or_options: str | TelemetryOptions) -> TelemetryClient:
    """Initialize the global IronTelemetry client."""
    global _client

    if isinstance(dsn_or_options, str):
        options = TelemetryOptions(dsn=dsn_or_options)
    else:
        options = dsn_or_options

    _client = TelemetryClient(options)
    return _client


def get_client() -> Optional[TelemetryClient]:
    """Get the global client instance."""
    return _client


def capture_exception(
    error: BaseException,
    extra: Optional[Dict[str, Any]] = None,
) -> SendResult:
    """Capture an exception using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return SendResult(success=False, error="Client not initialized")
    return _client.capture_exception(error, extra)


def capture_message(
    message: str,
    level: SeverityLevel = SeverityLevel.INFO,
) -> SendResult:
    """Capture a message using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return SendResult(success=False, error="Client not initialized")
    return _client.capture_message(message, level)


def add_breadcrumb(
    message: str,
    category: BreadcrumbCategory = BreadcrumbCategory.CUSTOM,
    level: SeverityLevel = SeverityLevel.INFO,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Add a breadcrumb using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return
    _client.add_breadcrumb(message, category, level, data)


def set_user(
    id: str,
    email: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Set user context using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return
    _client.set_user(id, email, data)


def clear_user() -> None:
    """Clear user context using the global client."""
    if _client:
        _client.clear_user()


def set_tag(key: str, value: str) -> None:
    """Set a tag using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return
    _client.set_tag(key, value)


def set_extra(key: str, value: Any) -> None:
    """Set extra context using the global client."""
    if not _client:
        print("[IronTelemetry] Client not initialized. Call init() first.", file=sys.stderr)
        return
    _client.set_extra(key, value)


def start_journey(name: str) -> JourneyScope:
    """Start a journey using the global client."""
    if not _client:
        raise RuntimeError("[IronTelemetry] Client not initialized. Call init() first.")
    return _client.start_journey(name)


def start_step(name: str, category: Optional[str] = None) -> Step:
    """Start a step in the current journey using the global client."""
    if not _client:
        raise RuntimeError("[IronTelemetry] Client not initialized. Call init() first.")
    return _client.start_step(name, category)


def flush() -> None:
    """Flush pending events using the global client."""
    if _client:
        _client.flush()


def close() -> None:
    """Close the global client."""
    global _client
    if _client:
        _client.close()
        _client = None


def use_unhandled_exception_handler() -> None:
    """Set up global unhandled exception handler."""
    original_hook = sys.excepthook

    def exception_handler(
        exc_type: type,
        exc_value: BaseException,
        exc_traceback: Any,
    ) -> None:
        """Handle uncaught exceptions."""
        if _client:
            _client.capture_exception(exc_value)
            _client.flush()

        # Call the original hook
        original_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler


def track_step(
    name: str,
    fn: Callable[[], T],
    category: Optional[str] = None,
) -> T:
    """Track a step with automatic error handling."""
    if not _client:
        return fn()

    with start_step(name, category) as step:
        try:
            return fn()
        except Exception:
            step.fail()
            raise
