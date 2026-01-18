
import json
from datetime import datetime
from .sqlite_backend import SQLiteBackend

class StateManager:
    """
    Manages persistent, atomic state for processes.
    Built on top of the SQLite backend.
    """

    def __init__(self, backend: SQLiteBackend):
        self.backend = backend
        self._init_schema()

    def _init_schema(self):
        """Ensure the process_state table exists."""
        conn = self.backend.get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS process_state (
                    trace_id TEXT PRIMARY KEY,
                    state_data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            # This doesn't close the connection, just the cursor context
            pass

    def get_state(self, trace_id: str) -> dict:
        """
        Get the current state for a given trace_id.
        Returns an empty dict if no state is found.
        """
        rows = self.backend.query('process_state', {'trace_id': trace_id})
        if not rows:
            return {}
        return json.loads(rows[0]['state_data'])

    def save_state(self, trace_id: str, state: dict):
        """
        Directly save or overwrite the state for a trace_id.
        This is a simple overwrite and is NOT transaction-safe for updates.
        """
        conn = self.backend.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO process_state (trace_id, state_data, updated_at)
                VALUES (?, ?, ?)
            """, (
                trace_id,
                json.dumps(state),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        finally:
            cursor.close()

    def update_state(self, trace_id: str, new_state: dict, merge: bool = True):
        """
        Atomically update process state using a database transaction.
        """
        conn = self.backend.get_connection()
        cursor = conn.cursor()

        try:
            # BEGIN IMMEDIATE locks the database for writing
            cursor.execute("BEGIN IMMEDIATE")

            if merge:
                # Read current state within the transaction
                cursor.execute(
                    "SELECT state_data FROM process_state WHERE trace_id=?",
                    (trace_id,)
                )
                row = cursor.fetchone()

                if row:
                    current = json.loads(row[0])
                    current.update(new_state)
                    state_to_save = current
                else:
                    state_to_save = new_state
            else:
                # If not merging, just use the new state
                state_to_save = new_state

            # Write the updated state
            cursor.execute("""
                INSERT OR REPLACE INTO process_state (trace_id, state_data, updated_at)
                VALUES (?, ?, ?)
            """, (
                trace_id,
                json.dumps(state_to_save),
                datetime.utcnow().isoformat()
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update state for {trace_id}: {e}")
        finally:
            cursor.close()
