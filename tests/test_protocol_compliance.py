"""
Test suite for protocol compliance.
Verifies that all event types are properly registered and used.
"""

import pytest
import sys
import ast
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.events import Events


import collections.abc

def test_events_all_returns_set():
    """Events.all() should return a set or frozenset."""
    all_events = Events.all()
    assert isinstance(all_events, collections.abc.Set)
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
    """handler.py should not contain magic string event types in code (not docstrings)."""
    import src.transport.handler as handler
    import inspect

    source = inspect.getsource(handler)
    tree = ast.parse(source)

    # Extract only string literals from actual code (not docstrings/comments)
    string_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value)

    # These values should NOT appear as string literals in code
    forbidden_values = [
        "system_ping",
        "system_pong",
        "echo_payload",
        "emergency_shutdown"
    ]

    for forbidden in forbidden_values:
        assert forbidden not in string_literals, \
            f"Found magic string '{forbidden}' in handler.py code - " \
            f"use Events.{forbidden.upper()} constant instead. " \
            f"All string literals found: {string_literals}"


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
