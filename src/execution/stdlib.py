import asyncio
import time
import uuid
import logging
from src.decision.context import DecisionContext
from src.execution.registry import action

logger = logging.getLogger(__name__)

# Note: These use the default registry via @action decorator

@action("system_ping")
async def system_ping(context: DecisionContext) -> dict:
    """Health check action - returns pong with timestamp."""
    return {
        "status": "success",
        "message": "pong",
        "timestamp": time.time(),
        "agent_id": context.decision_input.get("agent_id")
    }

@action("echo_payload")
async def echo_payload(context: DecisionContext) -> dict:
    """Debug action - echoes back the input payload."""
    return {
        "status": "success",
        "echo": context.decision_input.get("payload")
    }

@action("log_message")
async def log_message(context: DecisionContext) -> dict:
    """Logs a message at specified level (info/warning/error)."""
    payload = context.decision_input.get("payload", {})
    level = payload.get("level", "info")
    message = payload.get("message", "")

    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)

    return {
        "status": "success",
        "logged": True,
        "level": level
    }

@action("mock_deploy")
async def mock_deploy(context: DecisionContext) -> dict:
    """Simulates a deployment process with configurable duration."""
    payload = context.decision_input.get("payload", {})
    duration = payload.get("duration", 2)

    logger.info(f"Starting mock deployment (duration: {duration}s)")
    await asyncio.sleep(duration)
    logger.info("Mock deployment complete")

    return {
        "status": "success",
        "deployment_id": str(uuid.uuid4()),
        "duration": duration
    }

@action("emergency_shutdown")
async def emergency_shutdown(context: DecisionContext) -> dict:
    """Initiates emergency shutdown (immediate or graceful)."""
    payload = context.decision_input.get("payload", {})
    severity = payload.get("severity", "normal")

    if severity == "critical":
        logger.critical("CRITICAL: Emergency shutdown initiated")
        return {
            "status": "shutdown",
            "mode": "immediate",
            "delay": 0
        }
    else:
        logger.warning("Emergency shutdown scheduled (graceful)")
        await asyncio.sleep(5)  # Simulate cleanup
        return {
            "status": "shutdown",
            "mode": "graceful",
            "delay": 5
        }
