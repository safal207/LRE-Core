import pytest
import tempfile
import os
from src.storage.db import Database
from src.core.events import Events


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    db = Database(db_path)
    yield db

    # Cleanup
    os.unlink(db_path)


def test_database_initialization(temp_db):
    """Database should initialize with schema."""
    stats = temp_db.get_stats()
    assert stats['total_events'] == 0
    assert stats['unique_traces'] == 0


def test_log_inbound_event(temp_db):
    """Should log inbound events correctly."""
    event_id = temp_db.log_event(
        trace_id='test-trace-123',
        event_type=Events.SYSTEM_PING,
        direction='INBOUND',
        payload={'agent_id': 'agent-001'}
    )

    assert event_id > 0

    # Verify it was logged
    stats = temp_db.get_stats()
    assert stats['total_events'] == 1


def test_log_outbound_event(temp_db):
    """Should log outbound events correctly."""
    temp_db.log_event(
        trace_id='test-trace-123',
        event_type=Events.SYSTEM_PONG,
        direction='OUTBOUND',
        payload={'message': 'pong'}
    )

    events = temp_db.fetch_history(trace_id='test-trace-123')
    assert len(events) == 1
    assert events[0]['type'] == Events.SYSTEM_PONG
    assert events[0]['direction'] == 'OUTBOUND'


def test_fetch_history_by_trace_id(temp_db):
    """Should fetch events filtered by trace_id."""
    # Log events for two different traces
    temp_db.log_event('trace-1', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'A'})
    temp_db.log_event('trace-1', Events.SYSTEM_PONG, 'OUTBOUND', {})
    temp_db.log_event('trace-2', Events.ECHO_PAYLOAD, 'INBOUND', {'agent_id': 'B'})

    # Fetch only trace-1 events
    events = temp_db.fetch_history(trace_id='trace-1')
    assert len(events) == 2
    assert all(e['trace_id'] == 'trace-1' for e in events)


def test_fetch_history_by_agent_id(temp_db):
    """Should fetch events filtered by agent_id."""
    temp_db.log_event('t1', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'agent-A'})
    temp_db.log_event('t2', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'agent-B'})
    temp_db.log_event('t3', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'agent-A'})

    events = temp_db.fetch_history(agent_id='agent-A')
    assert len(events) == 2
    assert all(e['payload']['agent_id'] == 'agent-A' for e in events)


def test_fetch_history_with_limit(temp_db):
    """Should respect limit parameter."""
    for i in range(10):
        temp_db.log_event(f'trace-{i}', Events.SYSTEM_PING, 'INBOUND', {})

    events = temp_db.fetch_history(limit=5)
    assert len(events) == 5


def test_get_recent_agents(temp_db):
    """Should detect active agents."""
    import time

    # Agent A is active
    temp_db.log_event('t1', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'agent-A'})

    # Agent B was active 40 seconds ago (simulate with manual timestamp)
    old_time = time.time() - 40
    temp_db.log_event('t2', Events.SYSTEM_PING, 'INBOUND', {'agent_id': 'agent-B'})

    # Manually update timestamp for agent-B to be old
    import sqlite3
    with sqlite3.connect(temp_db.db_path) as conn:
        conn.execute(
            "UPDATE events SET created_at = ? WHERE trace_id = 't2'",
            (old_time,)
        )
        conn.commit()

    agents = temp_db.get_recent_agents(since_seconds=30)

    # Should have both agents
    assert len(agents) == 2

    # Agent A should be ONLINE
    agent_a = next(a for a in agents if a['agent_id'] == 'agent-A')
    assert agent_a['status'] == 'ONLINE'

    # Agent B should be OFFLINE
    agent_b = next(a for a in agents if a['agent_id'] == 'agent-B')
    assert agent_b['status'] == 'OFFLINE'


def test_database_stats(temp_db):
    """Should return correct statistics."""
    temp_db.log_event('t1', Events.SYSTEM_PING, 'INBOUND', {})
    temp_db.log_event('t1', Events.SYSTEM_PONG, 'OUTBOUND', {})
    temp_db.log_event('t2', Events.ECHO_PAYLOAD, 'INBOUND', {})

    stats = temp_db.get_stats()

    assert stats['total_events'] == 3
    assert stats['unique_traces'] == 2
    assert Events.SYSTEM_PING in stats['event_types']
    assert stats['event_types'][Events.SYSTEM_PING] == 1


def test_json_payload_serialization(temp_db):
    """Should correctly serialize/deserialize complex JSON payloads."""
    complex_payload = {
        'agent_id': 'test',
        'nested': {
            'key': 'value',
            'array': [1, 2, 3]
        },
        'number': 42
    }

    temp_db.log_event(
        'test-trace',
        Events.ECHO_PAYLOAD,
        'INBOUND',
        payload=complex_payload
    )

    events = temp_db.fetch_history(trace_id='test-trace')
    retrieved_payload = events[0]['payload']

    assert retrieved_payload == complex_payload
    assert isinstance(retrieved_payload['nested']['array'], list)


def test_empty_payload(temp_db):
    """Should handle events without payload."""
    temp_db.log_event('test', Events.SYSTEM_PING, 'INBOUND')

    events = temp_db.fetch_history()
    assert events[0]['payload'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])