"""Test connection pooling behavior."""

import threading
import pytest
from src.storage.sqlite_backend import SQLiteBackend


def test_connection_reuse_within_thread():
    """Test that connections are reused within the same thread."""
    backend = SQLiteBackend(":memory:")

    # Get connection twice
    conn1 = backend.get_connection()
    conn2 = backend.get_connection()

    # Should be the same connection object
    assert conn1 is conn2, "Connections should be reused within same thread"


def test_different_connections_across_threads():
    """Test that different threads get different connections."""
    backend = SQLiteBackend(":memory:")

    connections = []

    def get_connection_id():
        conn = backend.get_connection()
        connections.append(id(conn))

    # Create 5 threads
    threads = [threading.Thread(target=get_connection_id) for _ in range(5)]

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # All connections should be different
    assert len(set(connections)) == 5, "Each thread should have its own connection"


def test_connection_cleanup():
    """Test that connections can be properly closed."""
    backend = SQLiteBackend(":memory:")

    # Get connection
    conn = backend.get_connection()
    assert conn is not None

    # Close connection
    backend.close_connection()

    # Getting connection again should create new one
    new_conn = backend.get_connection()
    assert new_conn is not None
    assert new_conn is not conn  # Should be different object


def test_health_check():
    """Test database health check."""
    backend = SQLiteBackend(":memory:")

    assert backend.health_check() is True

    # Close connection
    backend.close_connection()

    # Health check should still work (creates new connection)
    assert backend.health_check() is True
