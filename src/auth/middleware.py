"""
WebSocket Authentication Middleware
Handles token verification and RBAC for WebSocket connections
"""
import json
import logging
from typing import Dict, Optional, Callable, Any, Awaitable
from src.auth.jwt_handler import jwt_handler
from src.auth.rbac import check_permission
from src.core.events import Events

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Middleware for WebSocket authentication and authorization"""

    def __init__(self, user_store=None):
        self.user_store = user_store

    async def authenticate(self, websocket) -> Optional[Dict]:
        """
        Authenticate a new connection
        Expects an 'auth' message as the first message
        """
        try:
            # Wait for the first message which should be the auth message
            message_text = await websocket.recv()
            message = json.loads(message_text)

            if message.get("type") != Events.AUTH_REQUEST:
                await self._send_error(websocket, "Authentication required", "AUTH_REQUIRED")
                return None

            token = message.get("payload", {}).get("token")
            if not token:
                await self._send_error(websocket, "Token missing", "TOKEN_MISSING")
                return None

            # Verify token
            try:
                payload = jwt_handler.verify_token(token)

                # Success response
                await websocket.send(json.dumps({
                    "type": Events.AUTH_SUCCESS,
                    "trace_id": message.get("trace_id"),
                    "payload": {
                        "user_id": payload["sub"],
                        "username": payload["username"],
                        "role": payload["role"]
                    }
                }))

                return payload

            except ValueError as e:
                await self._send_error(websocket, str(e), "INVALID_TOKEN")
                return None

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def authorize(self, role: str, event_type: str) -> bool:
        """Check if a role has permission for an event type"""
        return check_permission(role, event_type)

    async def _send_error(self, websocket, message: str, code: str):
        """Send authentication error and close connection"""
        await websocket.send(json.dumps({
            "type": Events.AUTH_FAILURE,
            "payload": {
                "error": message,
                "code": code
            }
        }))
        # In some cases we might want to close the connection,
        # but for now we'll let the handler decide.
