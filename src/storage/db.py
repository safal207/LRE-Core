"""
LRE Core Persistence Layer
Simple, async-ready SQLite wrapper for event logging.
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Single-responsibility persistence layer for LTP events.

    Design principles:
    - No ORM overhead
    - Async-compatible (uses thread pool in production)
    - Single table for simplicity
    - JSON for flexibility
    """

    def __init__(self, db_path: str = "data/lre.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_schema()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """Initialize database schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"

        with sqlite3.connect(self.db_path) as conn:
            if schema_path.exists():
                with open(schema_path) as f:
                    conn.executescript(f.read())
                logger.info(f"Database initialized: {self.db_path}")
            else:
                logger.warning(f"schema.sql not found at {schema_path}")

    def log_event(
        self,
        trace_id: str,
        event_type: str,
        direction: str,
        payload: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> int:
        """
        Log an event to the database.

        Args:
            trace_id: Session identifier (UUID)
            event_type: Event type from Events class
            direction: 'INBOUND' or 'OUTBOUND'
            payload: Event payload (will be JSON serialized)
            meta: Optional metadata
            timestamp: ISO 8601 timestamp (auto-generated if None)

        Returns:
            Event ID (auto-incremented primary key)
        """
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + 'Z'

        created_at = time.time()

        payload_json = json.dumps(payload) if payload else None
        meta_json = json.dumps(meta) if meta else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO events (trace_id, type, timestamp, direction, payload, meta, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (trace_id, event_type, timestamp, direction, payload_json, meta_json, created_at)
            )
            event_id = cursor.lastrowid
            conn.commit()

        logger.debug(f"Logged {direction} event: {event_type} (trace={trace_id[:8]}...)")
        return event_id

    def fetch_history(
        self,
        trace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch event history with optional filters.

        Args:
            trace_id: Filter by session ID
            agent_id: Filter by agent ID (extracted from payload)
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events (most recent first)
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if trace_id:
            query += " AND trace_id = ?"
            params.append(trace_id)

        if agent_id:
            query += " AND json_extract(payload, '$.agent_id') = ?"
            params.append(agent_id)

        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)

            events = []
            for row in cursor.fetchall():
                event = dict(row)
                # Deserialize JSON fields
                if event['payload']:
                    event['payload'] = json.loads(event['payload'])
                if event['meta']:
                    event['meta'] = json.loads(event['meta'])
                events.append(event)

        logger.debug(f"Fetched {len(events)} events (limit={limit})")
        return events

    def get_recent_agents(self, since_seconds: int = 30) -> List[Dict[str, Any]]:
        """
        Get list of agents that sent system_ping recently.

        Args:
            since_seconds: Time window for "recent" activity

        Returns:
            List of agent status dicts with keys:
            - agent_id: Agent identifier
            - last_ping: Unix timestamp of last ping
            - status: 'ONLINE' or 'OFFLINE'
        """
        cutoff_time = time.time() - since_seconds

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    json_extract(payload, '$.agent_id') as agent_id,
                    MAX(created_at) as last_ping,
                    COUNT(*) as ping_count
                FROM events
                WHERE type = 'system_ping'
                  AND json_extract(payload, '$.agent_id') IS NOT NULL
                GROUP BY json_extract(payload, '$.agent_id')
                """,
            )

            agents = []
            for row in cursor.fetchall():
                agent_id = row['agent_id']
                last_ping = row['last_ping']

                agents.append({
                    'agent_id': agent_id,
                    'last_ping': last_ping,
                    'status': 'ONLINE' if last_ping >= cutoff_time else 'OFFLINE',
                    'ping_count': row['ping_count']
                })

        logger.debug(f"Found {len(agents)} agents in history")
        return agents

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with keys: total_events, unique_traces, event_types
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT trace_id) FROM events")
            unique_traces = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT type, COUNT(*) as count
                FROM events
                GROUP BY type
                ORDER BY count DESC
                """
            )
            event_types = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            'total_events': total_events,
            'unique_traces': unique_traces,
            'event_types': event_types,
            'db_path': self.db_path
        }


# Singleton instance (optional, for convenience)
_db_instance: Optional[Database] = None

def get_db(db_path: str = "data/lre.db") -> Database:
    """Get or create singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
