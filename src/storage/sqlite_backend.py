
import threading
import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SQLiteBackend:
    """SQLite backend with thread-local connection pooling."""

    def __init__(self, db_path: str = "data/lre.db"):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file (or ":memory:" for in-memory)
        """
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock() # For thread-safe initialization
        self._ensure_data_dir()
        self._init_schema()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self):
        """
        Initialize database schema from schema.sql.
        Uses a temporary connection to avoid interfering with the pool.
        This operation is locked to be thread-safe.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Check if schema is already initialized
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
                if cursor.fetchone():
                    return

                schema_path = Path(__file__).parent / "schema.sql"
                if schema_path.exists():
                    with open(schema_path) as f:
                        conn.executescript(f.read())
                    logger.info(f"Database schema initialized in: {self.db_path}")
                else:
                    logger.warning(f"schema.sql not found at {schema_path}")
            finally:
                conn.close()

    def get_connection(self):
        """
        Get thread-local database connection (reuses connections).
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            logger.debug(f"Creating new SQLite connection for thread {threading.get_ident()}")
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False, # Allows use in multiple threads
                timeout=30.0,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def close_connection(self):
        """Close the database connection for the current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            logger.debug(f"Closing SQLite connection for thread {threading.get_ident()}")
            self._local.connection.close()
            self._local.connection = None

    def __del__(self):
        """Cleanup: close connection when backend is destroyed."""
        self.close_connection()

    def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.close_connection() # Close broken connection
            return False

    def execute(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return all results as a list of dicts.
        Handles connection and cursor management.
        NOTE: For non-SELECT statements, it commits automatically.
        For more complex transactions, use get_connection() and manage manually.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or ())

            if cursor.description:
                return [dict(row) for row in cursor.fetchall()]
            else:
                # This is an INSERT, UPDATE, or DELETE
                conn.commit()
                return []
        except Exception as e:
            conn.rollback()
            logger.error(f"SQL execute failed for '{sql[:100]}': {e}")
            raise
        finally:
            cursor.close()

    def query(self, table: str, conditions: dict = None):
        """
        Query table with parameterized queries (SQL injection safe).

        Args:
            table: Table name to query
            conditions: Dictionary of WHERE conditions (optional)

        Returns:
            List of matching rows

        Example:
            results = backend.query('messages', {'trace_id': 'abc-123', 'type': 'ping'})
        """
        if not conditions:
            sql = f"SELECT * FROM {table}"
            return self.execute(sql)

        # Use parameterized queries with ? placeholders
        placeholders = " AND ".join([f"{k}=?" for k in conditions.keys()])
        sql = f"SELECT * FROM {table} WHERE {placeholders}"
        values = tuple(conditions.values())

        return self.execute(sql, values)

    def log_event(
        self,
        trace_id: str,
        event_type: str,
        direction: str,
        payload: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> int:
        """Logs an event, returning its ID."""
        if timestamp is None:
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        created_at = time.time()
        payload_json = json.dumps(payload) if payload else None
        meta_json = json.dumps(meta) if meta else None

        sql = """
            INSERT INTO events (trace_id, type, timestamp, direction, payload, meta, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (trace_id, event_type, timestamp, direction, payload_json, meta_json, created_at)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            event_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Logged {direction} event: {event_type} (trace={trace_id[:8]}...)")
            return event_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


    def fetch_history(
        self,
        trace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches event history with optional filters."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if trace_id:
            query += " AND trace_id = ?"
            params.append(trace_id)
        if agent_id:
            query += " AND json_extract(payload, '$.agent_id') = ?"
            params.append(str(agent_id)) # Ensure it's a string for JSON query
        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        results = self.execute(query, tuple(params))

        # Deserialize JSON fields
        for event in results:
            if event.get('payload'):
                event['payload'] = json.loads(event['payload'])
            if event.get('meta'):
                event['meta'] = json.loads(event['meta'])

        logger.debug(f"Fetched {len(results)} events (limit={limit})")
        return results

    def get_recent_agents(self, since_seconds: int = 30) -> List[Dict[str, Any]]:
        """Get list of agents that sent system_ping recently."""
        cutoff_time = time.time() - since_seconds

        sql = """
            SELECT
                json_extract(payload, '$.agent_id') as agent_id,
                MAX(created_at) as last_ping,
                COUNT(*) as ping_count
            FROM events
            WHERE type = 'system_ping'
              AND json_extract(payload, '$.agent_id') IS NOT NULL
            GROUP BY json_extract(payload, '$.agent_id')
        """

        rows = self.execute(sql)

        agents = []
        for row in rows:
            agents.append({
                'agent_id': row['agent_id'],
                'last_ping': row['last_ping'],
                'status': 'ONLINE' if row['last_ping'] >= cutoff_time else 'OFFLINE',
                'ping_count': row['ping_count']
            })

        logger.debug(f"Found {len(agents)} agents in history")
        return agents

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        total_events = self.execute("SELECT COUNT(*) as c FROM events")[0]['c']
        unique_traces = self.execute("SELECT COUNT(DISTINCT trace_id) as c FROM events")[0]['c']

        type_counts = self.execute(
            """
            SELECT type, COUNT(*) as count
            FROM events
            GROUP BY type
            ORDER BY count DESC
            """
        )
        event_types = {row['type']: row['count'] for row in type_counts}

        return {
            'total_events': total_events,
            'unique_traces': unique_traces,
            'event_types': event_types,
            'db_path': self.db_path
        }

    def get_history_stats(
        self,
        trace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> Dict[str, int]:
        """Get stats for a filtered set of events, plus global total."""
        # Global count
        global_count = self.execute("SELECT COUNT(*) as c FROM events")[0]['c']

        # Filtered counts
        query = "SELECT COUNT(*) as total, COUNT(DISTINCT trace_id) as traces, COUNT(DISTINCT type) as types FROM events WHERE 1=1"
        params = []
        if trace_id:
            query += " AND trace_id = ?"
            params.append(trace_id)
        if agent_id:
            query += " AND json_extract(payload, '$.agent_id') = ?"
            params.append(str(agent_id))
        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        res = self.execute(query, tuple(params))

        return {
            "global_total": global_count,
            "filtered_total": res[0]['total'],
            "filtered_traces": res[0]['traces'],
            "filtered_types": res[0]['types']
        }
