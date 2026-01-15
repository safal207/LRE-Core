"""
Integration test for full message loop.
Tests that protocol changes don't break the system.
"""

import pytest
from src.core.events import Events
from src.transport.handler import validate_message
from datetime import datetime


class TestProtocolValidation:
    """Test suite for LTP protocol validation."""

    def test_valid_ping_message(self):
        """Test that a valid ping message passes validation."""
        ping_msg = {
            "trace_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": Events.SYSTEM_PING,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": {}
        }

        is_valid, error = validate_message(ping_msg)
        assert is_valid is True, f"Valid message rejected with error: {error}"
        assert error is None

    def test_valid_echo_message(self):
        """Test that a valid echo message passes validation."""
        echo_msg = {
            "trace_id": "test-trace-12345678",
            "type": Events.ECHO_PAYLOAD,
            "timestamp": "2025-01-14T10:30:00.000Z",
            "payload": {
                "test_data": "hello world",
                "nested": {"value": 42}
            },
            "meta": {
                "source": "test_suite"
            }
        }

        is_valid, error = validate_message(echo_msg)
        assert is_valid is True
        assert error is None


class TestInvalidMessages:
    """Test suite for invalid message rejection."""

    def test_missing_trace_id(self):
        """Test that message without trace_id is rejected."""
        invalid_msg = {
            "type": Events.SYSTEM_PING,
            "timestamp": datetime.utcnow().isoformat() + "Z"
            # Missing trace_id!
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E006", "Should return E006 for missing required field"

    def test_missing_type(self):
        """Test that message without type is rejected."""
        invalid_msg = {
            "trace_id": "test-123-45678",
            "timestamp": datetime.utcnow().isoformat() + "Z"
            # Missing type!
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E006"

    def test_missing_timestamp(self):
        """Test that message without timestamp is rejected."""
        invalid_msg = {
            "trace_id": "test-123-45678",
            "type": Events.SYSTEM_PING
            # Missing timestamp!
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E006"

    def test_invalid_event_type(self):
        """Test that unknown event type is rejected."""
        invalid_msg = {
            "trace_id": "test-123-45678",
            "type": "unknown_event_type_that_does_not_exist",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E002", "Should return E002 for unknown event type"

    def test_wrong_type_for_trace_id(self):
        """Test that non-string trace_id is rejected."""
        invalid_msg = {
            "trace_id": 12345,  # Should be string!
            "type": Events.SYSTEM_PING,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E007", "Should return E007 for type mismatch"

    def test_wrong_type_for_payload(self):
        """Test that non-dict payload is rejected."""
        invalid_msg = {
            "trace_id": "test-123-45678",
            "type": Events.ECHO_PAYLOAD,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": "this should be a dict, not a string"
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E007"

    def test_trace_id_too_short(self):
        """Test that trace_id with insufficient length is rejected."""
        invalid_msg = {
            "trace_id": "abc",  # Too short!
            "type": Events.SYSTEM_PING,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E007"

    def test_trace_id_invalid_characters(self):
        """Test that trace_id with invalid characters is rejected."""
        invalid_msg = {
            "trace_id": "test@#$%^&*()",  # Invalid characters!
            "type": Events.SYSTEM_PING,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E007"

    def test_not_a_dict(self):
        """Test that non-dict message is rejected."""
        invalid_msg = "this is a string, not a dict"

        is_valid, error = validate_message(invalid_msg)
        assert is_valid is False
        assert error == "E001", "Should return E001 for invalid JSON structure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
