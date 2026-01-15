"""Test SQL injection protection."""

import pytest
from src.storage.sqlite_backend import SQLiteBackend


def test_sql_injection_protection():
    """Test that malicious SQL in conditions is safely handled."""
    backend = SQLiteBackend(":memory:")

    # Create test table
    backend.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)

    # Insert test data
    backend.execute("INSERT INTO test_table (name) VALUES ('safe_data')")

    # Attempt SQL injection via conditions
    malicious_conditions = {
        "name": "'; DROP TABLE test_table; --"
    }

    # Should NOT drop the table, should safely return no results
    results = backend.query('test_table', malicious_conditions)

    # Verify table still exists and data is intact
    all_rows = backend.execute("SELECT * FROM test_table")
    assert len(all_rows) == 1
    assert all_rows[0]['name'] == 'safe_data'


def test_query_with_valid_conditions():
    """Test that normal queries still work correctly."""
    backend = SQLiteBackend(":memory:")

    backend.execute("""
        CREATE TABLE messages (
            trace_id TEXT,
            type TEXT,
            payload TEXT
        )
    """)

    # Insert test data
    backend.execute(
        "INSERT INTO messages (trace_id, type, payload) VALUES (?, ?, ?)",
        ('trace-123', 'ping', '{}')
    )
    backend.execute(
        "INSERT INTO messages (trace_id, type, payload) VALUES (?, ?, ?)",
        ('trace-456', 'echo', '{}')
    )

    # Query with conditions
    results = backend.query('messages', {'trace_id': 'trace-123'})

    assert len(results) == 1
    assert results[0]['trace_id'] == 'trace-123'
    assert results[0]['type'] == 'ping'
