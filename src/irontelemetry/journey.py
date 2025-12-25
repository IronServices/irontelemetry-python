"""Journey tracking for IronTelemetry SDK."""

from datetime import datetime
from typing import Any, Dict, Optional

from .config import generate_event_id
from .types import JourneyContext, User


class Journey:
    """Represents an active journey tracking session."""

    def __init__(self, name: str):
        self._id = generate_event_id()
        self._name = name
        self._started_at = datetime.now()
        self._metadata: Dict[str, Any] = {}
        self._user: Optional[User] = None
        self._current_step: Optional["Step"] = None
        self._completed = False
        self._failed = False

    def set_user(
        self,
        id: str,
        email: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> "Journey":
        """Set user context for this journey."""
        self._user = User(id=id, email=email, data=data)
        return self

    def set_metadata(self, key: str, value: Any) -> "Journey":
        """Set metadata for this journey."""
        self._metadata[key] = value
        return self

    def start_step(self, name: str, category: Optional[str] = None) -> "Step":
        """Start a new step in this journey."""
        # Complete any existing step
        if self._current_step and self._current_step._status == "in_progress":
            self._current_step._status = "completed"
            self._current_step._ended_at = datetime.now()

        step = Step(name, category, self)
        self._current_step = step
        return step

    def complete(self) -> None:
        """Mark the journey as completed."""
        if self._current_step and self._current_step._status == "in_progress":
            self._current_step._status = "completed"
            self._current_step._ended_at = datetime.now()
        self._completed = True

    def fail(self) -> None:
        """Mark the journey as failed."""
        if self._current_step and self._current_step._status == "in_progress":
            self._current_step._status = "failed"
            self._current_step._ended_at = datetime.now()
        self._failed = True

    def get_context(self) -> JourneyContext:
        """Get the journey context for an event."""
        return JourneyContext(
            journey_id=self._id,
            name=self._name,
            current_step=self._current_step._name if self._current_step else None,
            started_at=self._started_at,
            metadata=self._metadata,
        )

    def get_user(self) -> Optional[User]:
        """Get the user context for this journey."""
        return self._user

    @property
    def is_complete(self) -> bool:
        """Check if the journey is complete."""
        return self._completed or self._failed

    @property
    def journey_id(self) -> str:
        """Get journey ID."""
        return self._id


class Step:
    """Represents a step within a journey."""

    def __init__(self, name: str, category: Optional[str], journey: Journey):
        self._name = name
        self._category = category
        self._journey = journey
        self._started_at = datetime.now()
        self._ended_at: Optional[datetime] = None
        self._status = "in_progress"
        self._data: Dict[str, Any] = {}

    def set_data(self, key: str, value: Any) -> "Step":
        """Set data for this step."""
        self._data[key] = value
        return self

    def complete(self) -> None:
        """Mark the step as completed."""
        self._status = "completed"
        self._ended_at = datetime.now()

    def fail(self) -> None:
        """Mark the step as failed."""
        self._status = "failed"
        self._ended_at = datetime.now()

    @property
    def name(self) -> str:
        """Get the step name."""
        return self._name

    def get_journey(self) -> Journey:
        """Get the parent journey."""
        return self._journey

    def __enter__(self) -> "Step":
        """Enter the step context."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the step context."""
        if exc_type is not None:
            self.fail()
        elif self._status == "in_progress":
            self.complete()


class JourneyScope:
    """Journey scope that auto-completes on exit."""

    def __init__(self, journey: Journey, on_complete: Optional[callable] = None):
        self._journey = journey
        self._on_complete = on_complete

    def get_journey(self) -> Journey:
        """Get the underlying journey."""
        return self._journey

    def __enter__(self) -> "JourneyScope":
        """Enter the journey scope."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the journey scope."""
        if exc_type is not None:
            self._journey.fail()
        elif not self._journey.is_complete:
            self._journey.complete()

        if self._on_complete:
            self._on_complete()
