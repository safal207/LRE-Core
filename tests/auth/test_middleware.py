"""
Tests for Auth Middleware
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.auth.middleware import AuthMiddleware
from src.auth.jwt_handler import jwt_handler
from src.core.events import Events

@pytest.fixture
def middleware():
    return AuthMiddleware()

@pytest.mark.asyncio
async def test_authenticate_success(middleware):
    # Mock websocket
    websocket = AsyncMock()

    # Create valid token
    token = jwt_handler.create_access_token("user_1", "john", "admin")

    # Mock first message (auth_request)
    auth_request = {
        "type": Events.AUTH_REQUEST,
        "trace_id": "trace_1",
        "payload": {"token": token}
    }
    websocket.recv.return_value = json.dumps(auth_request)

    # Call authenticate
    payload = await middleware.authenticate(websocket)

    assert payload is not None
    assert payload["username"] == "john"
    assert payload["role"] == "admin"

    # Verify success message sent
    websocket.send.assert_called()
    sent_msg = json.loads(websocket.send.call_args[0][0])
    assert sent_msg["type"] == Events.AUTH_SUCCESS
    assert sent_msg["payload"]["username"] == "john"

@pytest.mark.asyncio
async def test_authenticate_failure_no_auth_msg(middleware):
    websocket = AsyncMock()

    # Send wrong message type
    websocket.recv.return_value = json.dumps({
        "type": "some_other_event",
        "trace_id": "trace_1"
    })

    payload = await middleware.authenticate(websocket)
    assert payload is None

    # Verify failure message sent
    websocket.send.assert_called()
    sent_msg = json.loads(websocket.send.call_args[0][0])
    assert sent_msg["type"] == Events.AUTH_FAILURE
    assert sent_msg["payload"]["code"] == "AUTH_REQUIRED"

@pytest.mark.asyncio
async def test_authenticate_failure_invalid_token(middleware):
    websocket = AsyncMock()

    # Send invalid token
    auth_request = {
        "type": Events.AUTH_REQUEST,
        "trace_id": "trace_1",
        "payload": {"token": "invalid-token"}
    }
    websocket.recv.return_value = json.dumps(auth_request)

    payload = await middleware.authenticate(websocket)
    assert payload is None

    # Verify failure message sent
    websocket.send.assert_called()
    sent_msg = json.loads(websocket.send.call_args[0][0])
    assert sent_msg["type"] == Events.AUTH_FAILURE
    assert sent_msg["payload"]["code"] == "INVALID_TOKEN"
