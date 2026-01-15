"""
Standard library of actions for LRE.
"""

import logging
import time  # ← КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ДОБАВЛЕН IMPORT
from src.decision.context import DecisionContext
from src.execution.registry import action
from src.core.events import Events
from src.storage.db import get_db

logger = logging.getLogger(__name__)

db = get_db()

# Note: These use the default registry via @action decorator

@action(Events.SYSTEM_PING)
async def system_ping(context: DecisionContext) -> dict:
    """Health check action - returns pong with timestamp."""
    return {
        "status": "success",
        "message": "pong",
        "timestamp": context.decision_input.get("timestamp"),
        "agent_id": context.decision_input.get("agent_id")
    }

@action(Events.ECHO_PAYLOAD)
async def echo_payload(context: DecisionContext) -> dict:
    """Debug action - echoes back the input payload."""
    return {
        "status": "success",
        "message": "echo",
        "payload": context.decision_input.get("payload", {})
    }

@action("mock_analyze")
async def mock_analyze(context: DecisionContext) -> dict:
    """Mock action to simulate long-running analysis."""
    import asyncio
    payload = context.decision_input.get("payload", {})
    duration = payload.get("duration", 2)

    await asyncio.sleep(duration)

    return {
        "status": "success",
        "message": "analysis_complete",
        "duration": duration,
        "result": {
            "confidence": 0.95,
            "findings": ["pattern_a", "pattern_b"]
        }
    }

@action("mock_deploy")
async def mock_deploy(context: DecisionContext) -> dict:
    """Mock action to simulate deployment."""
    import asyncio
    payload = context.decision_input.get("payload", {})
    duration = payload.get("duration", 1)

    await asyncio.sleep(duration)

    return {
        "status": "success",
        "message": "deployment_complete",
        "duration": duration
    }

@action(Events.EMERGENCY_SHUTDOWN)
async def emergency_shutdown(context: DecisionContext) -> dict:
    """Initiates emergency shutdown (immediate or graceful)."""
    payload = context.decision_input.get("payload", {})

    reason = payload.get("reason", "Emergency shutdown requested")
    admin_id = payload.get("admin_id", "unknown")

    logger.warning(f"EMERGENCY SHUTDOWN initiated by {admin_id}: {reason}")

    return {
        "status": "success",
        "message": "shutdown_initiated",
        "reason": reason,
        "admin_id": admin_id,
        "mode": "graceful",
        "delay": 5
    }

@action(Events.FETCH_HISTORY)
async def fetch_history(context: DecisionContext) -> dict:
    """
    Retrieve event history from database.

    Filters:
    - trace_id: Session-specific history
    - agent_id: Agent-specific history
    - type: Event type filter
    - limit: Max events (default 100)
    """
    payload = context.decision_input.get("payload", {})

    trace_id = payload.get("trace_id")
    agent_id = payload.get("agent_id")
    event_type = payload.get("type")
    limit = payload.get("limit", 100)

    # Fetch from database
    events = db.fetch_history(
        trace_id=trace_id,
        agent_id=agent_id,
        event_type=event_type,
        limit=limit
    )

    return {
        "type": Events.HISTORY_RESULT,
        "payload": {
            "events": events,
            "count": len(events),
            "filters": {
                "trace_id": trace_id,
                "agent_id": agent_id,
                "type": event_type,
                "limit": limit
            }
        }
    }


@action("get_agent_status")
async def get_agent_status(context: DecisionContext) -> dict:
    """
    Get list of recently active agents.
    """
    payload = context.decision_input.get("payload", {})
    since_seconds = payload.get("since_seconds", 30)

    agents = db.get_recent_agents(since_seconds=since_seconds)

    return {
        "type": "agent_status_result",
        "payload": {
            "agents": agents,
            "timestamp": time.time()  # ← ТЕПЕРЬ РАБОТАЕТ!
        }
    }


@action("get_db_stats")
async def get_db_stats(context: DecisionContext) -> dict:
    """
    Get database statistics for debugging.
    """
    stats = db.get_stats()

    return {
        "type": "db_stats_result",
        "payload": stats
    }
