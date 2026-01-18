import json
import logging
import asyncio
from datetime import datetime
import re
from typing import Optional, Tuple

from src.storage.sqlite_backend import SQLiteBackend
import websockets
from src.core.events import Events

logger = logging.getLogger(__name__)

db = SQLiteBackend()


def validate_message(msg: dict) -> tuple[bool, str | None]:
    """
    Validates LTP message structure and content.

    Args:
        msg: Message dictionary to validate

    Returns:
        Tuple of (is_valid, error_code)
        - is_valid: True if message is valid
        - error_code: Error code string if invalid, None otherwise

    Error codes:
        E001: Invalid JSON structure
        E002: Unknown event type
        E006: Required field missing
        E007: Field type mismatch
    """
    # Type check for msg itself
    if not isinstance(msg, dict):
        return False, "E001"

    # Check required fields presence
    required_fields = ['type', 'trace_id', 'timestamp']
    for field in required_fields:
        if field not in msg:
            return False, "E006"

    # Validate field types - type must be string
    if not isinstance(msg['type'], str):
        return False, "E007"

    # Validate field types - trace_id must be string
    if not isinstance(msg['trace_id'], str):
        return False, "E007"

    # Validate field types - timestamp must be string
    if not isinstance(msg['timestamp'], str):
        return False, "E007"

    # Validate trace_id format (basic check)
    # Should be at least 8 characters (minimal UUID representation)
    if len(msg['trace_id'].strip()) < 8:
        return False, "E007"

    # Validate trace_id contains alphanumeric and hyphens only
    if not re.match(r'^[a-zA-Z0-9\-]+$', msg['trace_id']):
        return False, "E007"

    # Validate event type is registered
    if not Events.is_valid(msg['type']):
        return False, "E002"

    # Validate payload type if present
    if 'payload' in msg:
        if not isinstance(msg['payload'], dict):
            return False, "E007"

    # Validate meta type if present
    if 'meta' in msg:
        if not isinstance(msg['meta'], dict):
            return False, "E007"
    return True, None

async def send_error(websocket, trace_id: str, error_code: str):
    """Send error response to client."""

    error_messages = {
        "E001": "Invalid JSON structure",
        "E002": "Unknown event type",
        "E003": "Unauthorized trace_id",
        "E004": "Runtime execution failure",
        "E005": "Database write failed",
        "E006": "Required field missing",
        "E007": "Field type mismatch"
    }

    error_msg = {
        "trace_id": trace_id,
        "type": Events.ERROR,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "code": error_code,
            "message": error_messages.get(error_code, "Unknown error"),
            "details": f"See PROTOCOL.md for error code {error_code}"
        }
    }

    # Log outbound error event
    db.log_event(
        trace_id=trace_id,
        event_type=Events.ERROR,
        direction='OUTBOUND',
        payload=error_msg.get('payload'),
        timestamp=error_msg.get('timestamp')
    )

    try:
        await websocket.send(json.dumps(error_msg))
    except Exception as e:
        logger.error(f"Failed to send error: {e}")

async def handle_message(websocket, msg: dict, runtime):
    """Handle incoming WebSocket message with validation."""
    # Validate message
    is_valid, error_code = validate_message(msg)
    if not is_valid:
        await send_error(websocket, msg.get('trace_id', 'unknown'), error_code)
        return

    # Log inbound event
    db.log_event(
        trace_id=msg.get('trace_id'),
        event_type=msg.get('type'),
        direction='INBOUND',
        payload=msg.get('payload'),
        timestamp=msg.get('timestamp')
    )

    msg_type = msg['type']

    if msg_type == Events.SYSTEM_PING:
        await handle_ping(websocket, msg, runtime)
    elif msg_type == Events.ECHO_PAYLOAD:
        await handle_echo(websocket, msg, runtime)
    elif msg_type == Events.EMERGENCY_SHUTDOWN:
        await handle_shutdown(websocket, msg, runtime)
    else:
        # If it's a valid event type but not explicitly handled here,
        # pass it to runtime as generic execution?
        # The spec implies specific handlers for these events.
        # But maybe we should support generic execution too?
        # For now, E002 is for UNKNOWN event type.
        # If Events.is_valid passed, it IS known.
        # So we should probably handle it or say "Not implemented".
        logger.warning(f"Event type {msg_type} valid but no specific handler. Passing to runtime.")
        await execute_via_runtime(websocket, msg, runtime)

async def execute_via_runtime(websocket, msg: dict, runtime, send_response: bool = True):
    """Helper to execute action via runtime."""
    # Construct decision input
    decision_input = {
        "action": msg['type'],
        "agent_id": msg.get("payload", {}).get("agent_id", "anonymous"),
        "payload": msg.get("payload", {}),
        "trace_id": msg['trace_id']
    }

    # Execute
    result = await runtime.process_decision(decision_input)

    if not send_response:
        return result

    # Format response
    # Pipeline execution returns summary where 'result' field contains LRE_DP output
    # LRE_DP output 'result' field contains the actual action return value
    dp_output = result.get("result", {})
    action_result = dp_output.get("result", dp_output)

    resp_type = msg['type']
    resp_payload = action_result

    # If action result is a protocol message (has type and payload), unwrap it
    if isinstance(action_result, dict) and 'type' in action_result and 'payload' in action_result:
        resp_type = action_result['type']
        resp_payload = action_result['payload']

    response = {
        "trace_id": msg['trace_id'],
        "type": resp_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": resp_payload
    }

    if result.get("status") == "failed":
        await send_error(websocket, msg['trace_id'], "E004")
    else:
        # Log outbound event
        db.log_event(
            trace_id=response['trace_id'],
            event_type=response['type'],
            direction='OUTBOUND',
            payload=response.get('payload'),
            timestamp=response.get('timestamp')
        )
        await websocket.send(json.dumps(response))

async def handle_ping(websocket, msg: dict, runtime):
    """Handle system_ping event."""
    # Execute in runtime for logging/persistence, but don't send standard response
    await execute_via_runtime(websocket, msg, runtime, send_response=False)

    # Send custom PONG response
    response = {
        "trace_id": msg['trace_id'],
        "type": Events.SYSTEM_PONG,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "server_timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }

    # Log outbound event
    db.log_event(
        trace_id=response['trace_id'],
        event_type=response['type'],
        direction='OUTBOUND',
        payload=response.get('payload'),
        timestamp=response.get('timestamp')
    )

    await websocket.send(json.dumps(response))

async def handle_echo(websocket, msg: dict, runtime):
    """Handle echo_payload event."""
    # Spec: Response: Same event with identical payload.

    response = {
        "trace_id": msg['trace_id'],
        "type": Events.ECHO_PAYLOAD,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": msg.get("payload", {})
    }

    # Log outbound event
    db.log_event(
        trace_id=response['trace_id'],
        event_type=response['type'],
        direction='OUTBOUND',
        payload=response.get('payload'),
        timestamp=response.get('timestamp')
    )

    await websocket.send(json.dumps(response))

async def handle_shutdown(websocket, msg: dict, runtime):
    """Handle emergency_shutdown event."""
    # Check auth? (Not implemented yet)

    logger.warning(f"Shutdown requested by trace_id {msg['trace_id']}")

    # Notify runtime?
    decision_input = {
        "action": Events.EMERGENCY_SHUTDOWN,
        "payload": msg.get("payload", {})
    }
    await runtime.process_decision(decision_input)

    # Close connection
    await websocket.close(1000, "Shutdown initiated")

    # Trigger runtime shutdown
    asyncio.create_task(runtime.shutdown())


async def handle_client(websocket, runtime):
    """
    Main WebSocket client handler.
    """
    remote_addr = getattr(websocket, 'remote_address', 'unknown')
    logger.info(f"New connection from {remote_addr}")

    try:
        async for message in websocket:
            try:
                msg = json.loads(message)
                await handle_message(websocket, msg, runtime)
            except json.JSONDecodeError:
                await send_error(websocket, "unknown", "E001")
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                await send_error(websocket, "unknown", "E004")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed: {remote_addr}")
    except Exception as e:
        logger.error(f"Connection error: {e}")
