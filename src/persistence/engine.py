import aiosqlite
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PersistenceEngine:
    """
    Async persistence layer for decision history.
    Subscribes to Event Bus and logs all decisions to SQLite.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "./data/lre_core.db"):
        self.db_path = Path(db_path)
        self.db: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database connection and schema."""
        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row  # Enable dict-like access

        # Initialize schema
        await self._init_schema()

        logger.info(f"Persistence engine initialized: {self.db_path}")

    async def _init_schema(self):
        """Create tables and indexes if they don't exist."""
        # Check schema version or create tables
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS decision_log (
                trace_id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('executed', 'failed', 'rejected', 'deferred')),
                input_payload TEXT,      -- JSON
                result_payload TEXT,      -- JSON
                latency_ms REAL,
                error_msg TEXT            -- NULL for successful executions
            );
        """)

        # Indexes for common queries
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON decision_log(agent_id);")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON decision_log(timestamp);")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_status ON decision_log(status);")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON decision_log(agent_id, timestamp DESC);")

        # Schema versioning table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at REAL NOT NULL
            );
        """)

        # Initialize schema version if empty
        async with self.db.execute("SELECT COUNT(*) FROM schema_version") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                await self.db.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (self.SCHEMA_VERSION, time.time())
                )

        await self.db.commit()

    async def log_decision(self, context: 'DecisionContext'): # type: ignore
        """
        Log a decision from DecisionContext object.
        Used for direct calls (not via Event Bus).
        """
        summary = context.get_summary()
        await self._insert_record(summary)

    async def log_decision_from_summary(self, summary: Dict[str, Any]):
        """
        Log a decision from event data (Event Bus callback).

        Args:
            summary: Decision summary dict from DecisionContext.get_summary()
        """
        await self._insert_record(summary)

    async def _insert_record(self, summary: Dict[str, Any]):
        """Internal method to write record to database."""
        if not self.db:
            logger.error("Database not initialized")
            return

        try:
            await self.db.execute(
                """INSERT INTO decision_log
                   (trace_id, timestamp, agent_id, action, status,
                    input_payload, result_payload, latency_ms, error_msg)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    summary["trace_id"],
                    time.time(),
                    summary["decision"].get("agent_id"),
                    summary["decision"].get("action"),
                    summary["status"],
                    json.dumps(summary["decision"]),
                    json.dumps(summary.get("result")),
                    summary.get("latency_ms"),
                    ", ".join(summary.get("errors", [])) if summary.get("errors") else None
                )
            )
            await self.db.commit()
            logger.debug(f"Logged decision {summary['trace_id']}")
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            # Don't crash - persistence failures shouldn't kill the runtime

    async def get_agent_history(
        self,
        agent_id: str,
        limit: int = 10,
        status: Optional[str] = None,
        action: Optional[str] = None,
        since_timestamp: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get agent decision history with optional filters.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of records (default: 10)
            status: Filter by status (executed/failed/rejected/deferred)
            action: Filter by action name
            since_timestamp: Only return decisions after this time

        Returns:
            List of decision records, newest first
        """
        if not self.db:
            return []

        query = """
            SELECT trace_id, timestamp, agent_id, action, status,
                   input_payload, result_payload, latency_ms, error_msg
            FROM decision_log
            WHERE agent_id = ?
        """
        params = [agent_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        if action:
            query += " AND action = ?"
            params.append(action)

        if since_timestamp:
            query += " AND timestamp > ?"
            params.append(since_timestamp)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

            # Convert rows to dicts and parse JSON fields
            results = []
            for row in rows:
                record = dict(row)
                record["input_payload"] = json.loads(record["input_payload"])
                if record["result_payload"]:
                    record["result_payload"] = json.loads(record["result_payload"])
                results.append(record)

            return results

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about logged decisions."""
        if not self.db:
            return {}

        async with self.db.execute("""
            SELECT
                COUNT(*) as total_decisions,
                COUNT(DISTINCT agent_id) as unique_agents,
                SUM(CASE WHEN status = 'executed' THEN 1 ELSE 0 END) as executed_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(latency_ms) as avg_latency_ms
            FROM decision_log
        """) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return {}

    async def _on_decision_event(self, topic: str, data: Dict[str, Any]):
        """
        Event handler for decision.* events.
        Automatically logs decisions when events are published.

        Args:
            topic: Event topic (e.g., "decision.completed")
            data: Decision summary from DecisionContext.get_summary()
        """
        await self.log_decision_from_summary(data)

    async def close(self):
        """Close database connection gracefully."""
        if self.db:
            await self.db.commit()
            await self.db.close()
            logger.info("Persistence engine closed")
