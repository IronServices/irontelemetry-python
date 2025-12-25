"""Breadcrumb management for IronTelemetry SDK."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import Breadcrumb, BreadcrumbCategory, SeverityLevel


class BreadcrumbManager:
    """Manages breadcrumbs for an SDK instance."""

    def __init__(self, max_breadcrumbs: int = 100):
        self._max_breadcrumbs = max_breadcrumbs
        self._breadcrumbs: List[Breadcrumb] = []

    def add(
        self,
        message: str,
        category: BreadcrumbCategory = BreadcrumbCategory.CUSTOM,
        level: SeverityLevel = SeverityLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a breadcrumb."""
        breadcrumb = Breadcrumb(
            timestamp=datetime.now(),
            category=category,
            message=message,
            level=level,
            data=data,
        )

        self._breadcrumbs.append(breadcrumb)

        # Trim to max size
        if len(self._breadcrumbs) > self._max_breadcrumbs:
            self._breadcrumbs = self._breadcrumbs[-self._max_breadcrumbs:]

    def add_breadcrumb(self, breadcrumb: Breadcrumb) -> None:
        """Add a full Breadcrumb object."""
        self._breadcrumbs.append(breadcrumb)

        if len(self._breadcrumbs) > self._max_breadcrumbs:
            self._breadcrumbs = self._breadcrumbs[-self._max_breadcrumbs:]

    def get_all(self) -> List[Breadcrumb]:
        """Get all breadcrumbs."""
        return list(self._breadcrumbs)

    def clear(self) -> None:
        """Clear all breadcrumbs."""
        self._breadcrumbs = []

    @property
    def count(self) -> int:
        """Get the number of breadcrumbs."""
        return len(self._breadcrumbs)
