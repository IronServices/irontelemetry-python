"""Configuration handling for IronTelemetry SDK."""

import uuid
from urllib.parse import urlparse

from .types import ParsedDsn, TelemetryOptions


def parse_dsn(dsn: str) -> ParsedDsn:
    """Parse a DSN string into its components.

    Format: https://pk_live_xxx@irontelemetry.com
    """
    try:
        parsed = urlparse(dsn)
        public_key = parsed.username

        if not public_key or not public_key.startswith("pk_"):
            raise ValueError("DSN must contain a valid public key starting with pk_")

        protocol = parsed.scheme
        host = parsed.hostname or ""

        return ParsedDsn(
            public_key=public_key,
            host=host,
            protocol=protocol,
            api_base_url=f"{protocol}://{host}",
        )
    except Exception as e:
        if "pk_" in str(e):
            raise
        raise ValueError(f"Invalid DSN format: {dsn}") from e


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def resolve_options(options: TelemetryOptions) -> tuple[TelemetryOptions, ParsedDsn]:
    """Validate and resolve options with defaults."""
    parsed_dsn = parse_dsn(options.dsn)

    # Clamp sample rate
    options.sample_rate = max(0.0, min(1.0, options.sample_rate))

    # Set API base URL if not provided
    if not options.api_base_url:
        options.api_base_url = parsed_dsn.api_base_url

    return options, parsed_dsn
