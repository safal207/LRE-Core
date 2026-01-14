"""
Canonical event registry for LTP (Liminal Transport Protocol).

This module serves as the single source of truth for all event types.
All event strings MUST be defined here and imported elsewhere.

Usage:
    from src.core.events import Events

    if message['type'] == Events.SYSTEM_PING:
        handle_ping()
"""

from typing import Set


class Events:
    """
    Event type constants for LTP protocol.

    These constants are used by:
    - handler.py (message routing)
    - runtime.py (event execution)
    - server_demo.py (testing)
    - EVENTS.md (documentation)

    DO NOT use string literals for event types elsewhere in codebase.
    """

    # System events - infrastructure and health checks
    SYSTEM_PING = "system_ping"
    SYSTEM_PONG = "system_pong"

    # User events - application logic
    ECHO_PAYLOAD = "echo_payload"
    LOG_MESSAGE = "log_message"
    MOCK_DEPLOY = "mock_deploy"

    # Control events - administrative actions
    EMERGENCY_SHUTDOWN = "emergency_shutdown"

    # Error events
    ERROR = "error"

    @classmethod
    def all(cls) -> Set[str]:
        """
        Returns set of all registered event types.

        Returns:
            Set of event type strings

        Example:
            >>> Events.all()
            {'system_ping', 'system_pong', 'echo_payload', ...}
        """
        return {
            value for key, value in cls.__dict__.items()
            if not key.startswith('_')
            and isinstance(value, str)
            and key.isupper()
        }

    @classmethod
    def is_valid(cls, event_type: str) -> bool:
        """
        Validates if an event type is registered.

        Args:
            event_type: Event type string to validate

        Returns:
            True if event type is registered, False otherwise

        Example:
            >>> Events.is_valid("system_ping")
            True
            >>> Events.is_valid("unknown_event")
            False
        """
        return event_type in cls.all()

    @classmethod
    def list_by_category(cls) -> dict:
        """
        Returns events organized by category.

        Returns:
            Dictionary with categories as keys and event lists as values
        """
        return {
            "system": [cls.SYSTEM_PING, cls.SYSTEM_PONG],
            "user": [cls.ECHO_PAYLOAD],
            "control": [cls.EMERGENCY_SHUTDOWN],
            "error": [cls.ERROR]
        }
