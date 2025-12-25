"""Type definitions for IronTelemetry SDK."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SeverityLevel(str, Enum):
    """Severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class BreadcrumbCategory(str, Enum):
    """Breadcrumb categories."""
    UI = "ui"
    HTTP = "http"
    NAVIGATION = "navigation"
    CONSOLE = "console"
    AUTH = "auth"
    BUSINESS = "business"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


@dataclass
class Breadcrumb:
    """A breadcrumb representing an event leading up to an error."""
    timestamp: datetime
    category: BreadcrumbCategory
    message: str
    level: SeverityLevel = SeverityLevel.INFO
    data: Optional[Dict[str, Any]] = None


@dataclass
class User:
    """User information for context."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class StackFrame:
    """Stack frame information."""
    function: Optional[str] = None
    filename: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None
    context: Optional[List[str]] = None


@dataclass
class ExceptionInfo:
    """Exception/error information."""
    type: str
    message: str
    stacktrace: Optional[List[StackFrame]] = None


@dataclass
class PlatformInfo:
    """Platform/runtime information."""
    name: str
    version: Optional[str] = None
    os: Optional[str] = None


@dataclass
class JourneyContext:
    """Journey context for tracking user flows."""
    journey_id: str
    name: str
    started_at: datetime
    current_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelemetryEvent:
    """Event payload sent to the server."""
    event_id: str
    timestamp: datetime
    level: SeverityLevel
    platform: PlatformInfo
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    breadcrumbs: List[Breadcrumb] = field(default_factory=list)
    message: Optional[str] = None
    exception: Optional[ExceptionInfo] = None
    user: Optional[User] = None
    journey: Optional[JourneyContext] = None
    environment: Optional[str] = None
    app_version: Optional[str] = None


@dataclass
class ParsedDsn:
    """Parsed DSN components."""
    public_key: str
    host: str
    protocol: str
    api_base_url: str


@dataclass
class SendResult:
    """Result of sending an event."""
    success: bool
    event_id: Optional[str] = None
    error: Optional[str] = None
    queued: bool = False


@dataclass
class TelemetryOptions:
    """Options for initializing the SDK."""
    dsn: str
    environment: str = "production"
    app_version: str = "0.0.0"
    sample_rate: float = 1.0
    max_breadcrumbs: int = 100
    debug: bool = False
    before_send: Optional[Callable[[TelemetryEvent], Optional[TelemetryEvent]]] = None
    enable_offline_queue: bool = True
    max_offline_queue_size: int = 500
    api_base_url: Optional[str] = None
