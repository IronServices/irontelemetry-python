# IronTelemetry SDK for Python

Error monitoring and crash reporting SDK for Python applications. Capture exceptions, track user journeys, and get insights to fix issues faster.

[![PyPI](https://img.shields.io/pypi/v/irontelemetry.svg)](https://pypi.org/project/irontelemetry/)
[![Python](https://img.shields.io/pypi/pyversions/irontelemetry.svg)](https://pypi.org/project/irontelemetry/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install irontelemetry
```

## Quick Start

### Basic Exception Capture

```python
import irontelemetry

# Initialize with your DSN
irontelemetry.init("https://pk_live_xxx@irontelemetry.com")

# Capture exceptions
try:
    do_something()
except Exception as e:
    irontelemetry.capture_exception(e)
    raise
```

### Journey Tracking

Track user journeys to understand the context of errors:

```python
import irontelemetry

# Track a complete user journey
with irontelemetry.start_journey("Checkout Flow"):
    irontelemetry.set_user("user-123", "user@example.com")

    with irontelemetry.start_step("Validate Cart", "business"):
        validate_cart()

    with irontelemetry.start_step("Process Payment", "business"):
        process_payment()

    with irontelemetry.start_step("Send Confirmation", "notification"):
        send_confirmation_email()
```

Any exceptions captured during the journey are automatically correlated.

## Configuration

```python
from irontelemetry import TelemetryOptions, init

init(TelemetryOptions(
    dsn="https://pk_live_xxx@irontelemetry.com",
    environment="production",
    app_version="1.2.3",
    sample_rate=1.0,  # 100% of events
    debug=False,
    before_send=lambda event: event if "expected" not in (event.message or "") else None,
))
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dsn` | str | required | Your Data Source Name |
| `environment` | str | 'production' | Environment name |
| `app_version` | str | '0.0.0' | Application version |
| `sample_rate` | float | 1.0 | Sample rate (0.0 to 1.0) |
| `max_breadcrumbs` | int | 100 | Max breadcrumbs to keep |
| `debug` | bool | False | Enable debug logging |
| `before_send` | callable | None | Hook to filter/modify events |
| `enable_offline_queue` | bool | True | Enable offline queue |
| `max_offline_queue_size` | int | 500 | Max offline queue size |

## Features

- **Automatic Exception Capture**: Capture and report exceptions with full stack traces
- **Journey Tracking**: Track user flows and correlate errors with context
- **Breadcrumbs**: Leave a trail of events leading up to an error
- **User Context**: Associate errors with specific users
- **Tags & Extras**: Add custom metadata to your events
- **Offline Queue**: Events are queued when offline and sent when connectivity returns
- **Async Support**: Full async/await support with `capture_exception_async` and `capture_message_async`
- **Type Hints**: Full type annotations for IDE support

## Breadcrumbs

```python
from irontelemetry import add_breadcrumb, BreadcrumbCategory

# Add breadcrumbs to understand what happened before an error
add_breadcrumb("User clicked checkout button", BreadcrumbCategory.UI)
add_breadcrumb("Payment API called", BreadcrumbCategory.HTTP)

# Or with full control
add_breadcrumb(
    "User logged in",
    category=BreadcrumbCategory.AUTH,
    level=SeverityLevel.INFO,
    data={"user_id": "123"},
)
```

## Global Exception Handling

```python
import irontelemetry

irontelemetry.init("your-dsn")
irontelemetry.use_unhandled_exception_handler()
```

This sets up a handler for `sys.excepthook` to capture uncaught exceptions.

## Helper Methods

```python
from irontelemetry import track_step

# Track a step with automatic error handling
track_step("Process Order", lambda: process_order())

# With return value
result = track_step("Calculate Total", lambda: calculate_total())
```

## Async Support

```python
import irontelemetry

# Async exception capture
await irontelemetry.capture_exception_async(error)

# Async message capture
await irontelemetry.capture_message_async("Something happened")

# Async flush
await irontelemetry.flush_async()
```

## Flushing

```python
# Flush pending events before app shutdown
irontelemetry.flush()
```

## Type Support

This package includes full type annotations:

```python
from irontelemetry import (
    TelemetryOptions,
    TelemetryEvent,
    Breadcrumb,
    SeverityLevel,
    BreadcrumbCategory,
)
```

## Python Version Support

- Python 3.8+
- Full type hints support
- async/await support

## Links

- [Documentation](https://www.irontelemetry.com/docs)
- [Dashboard](https://www.irontelemetry.com)

## License

MIT License - see [LICENSE](LICENSE) for details.
