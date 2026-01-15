"""
Test suite for protocol compliance.
Verifies that all event types are properly registered and used.
"""

import pytest
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.events import Events


def test_events_all_returns_set():
    """Events.all() should return a set."""
    all_events = Events.all()
    assert isinstance(all_events, set)
    assert len(all_events) > 0


def test_events_contains_required_types():
    """Events should contain all documented event types."""
    all_events = Events.all()

    required_events = {
        Events.SYSTEM_PING,
        Events.SYSTEM_PONG,
        Events.ECHO_PAYLOAD,
        Events.EMERGENCY_SHUTDOWN,
        Events.ERROR
    }

    assert required_events.issubset(all_events), \
        f"Missing events: {required_events - all_events}"


def test_events_is_valid():
    """Events.is_valid() should correctly validate event types."""
    assert Events.is_valid(Events.SYSTEM_PING) is True
    assert Events.is_valid("unknown_event") is False
    assert Events.is_valid("") is False
    assert Events.is_valid(None) is False


def test_no_magic_strings_in_handler():
    """handler.py should not contain magic string event types."""
    import src.transport.handler as handler
    import inspect

    source = inspect.getsource(handler)

    # These strings should NOT appear as literals
    # We check for the string literal with quotes
    # But be careful, Events.SYSTEM_PING IS the string "system_ping".
    # So if we use Events.SYSTEM_PING, the string literal "system_ping" might not appear in source code
    # UNLESS it is the definition of Events.SYSTEM_PING (which is in events.py, not handler.py).

    forbidden_literals = [
        '"system_ping"',
        "'system_ping'",
        '"system_pong"',
        "'system_pong'",
        '"echo_payload"',
        "'echo_payload'",
        '"emergency_shutdown"',
        "'emergency_shutdown'"
    ]

    for literal in forbidden_literals:
        assert literal not in source, \
            f"Found magic string {literal} in handler.py - use Events constants"


def test_events_list_by_category():
    """Events.list_by_category() should return organized events."""
    categories = Events.list_by_category()

    assert "system" in categories
    assert "user" in categories
    assert "control" in categories
    assert "error" in categories

    assert Events.SYSTEM_PING in categories["system"]
    assert Events.ECHO_PAYLOAD in categories["user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
