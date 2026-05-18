"""
WebSocket Authentication Middleware
Handles token verification and RBAC for WebSocket connections
"""
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Callable, Any, Awaitable
from src.auth.jwt_handler import jwt_handler
from src.auth.rbac import check_permission
from src.core.events import Events
from src.storage.user_store import user_store as default_user_store

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Middleware for WebSocket authentication and authorization"""

    def __init__(self, user_store=None):
        self.user_store = user_store or default_user_store
        # Simple in-memory brute force protection: username -> (attempts, last_attempt_time)
        self._login_attempts = {}
        self._lock = asyncio.Lock()

    async def _check_brute_force(self, username: str) -> bool:
        """Check if username is temporarily locked due to failed attempts"""
        async with self._lock:
            if username in self._login_attempts:
                attempts, last_time = self._login_attempts[username]
                if attempts >= 5:
                    elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
                    if elapsed < 300:  # 5 minutes lockout
                        return False
                    else:
                        # Lock expired
                        del self._login_attempts[username]
            return True

    async def _record_attempt(self, username: str, success: bool):
        """Record a login attempt"""
        async with self._lock:
            if success:
                if username in self._login_attempts:
                    del self._login_attempts[username]
            else:
                attempts, _ = self._login_attempts.get(username, (0, None))
                self._login_attempts[username] = (attempts + 1, datetime.now(timezone.utc))

    async def authenticate(self, websocket) -> Optional[Dict]:
        """
        Authenticate a new connection
        Expects an 'auth_request' or 'auth_login' message as the first message
        """
        try:
            # Wait for the first message which should be the auth message
            message_text = await websocket.recv()
            message = json.loads(message_text)
            msg_type = message.get("type")
            trace_id = message.get("trace_id", "unknown")

            if msg_type == Events.AUTH_LOGIN:
                return await self._handle_login(websocket, message)
            elif msg_type == Events.AUTH_REQUEST:
                return await self._handle_token_auth(websocket, message)
            else:
                await self._send_error(websocket, "Authentication required", "AUTH_REQUIRED")
                return None

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def _handle_login(self, websocket, message: Dict) -> Optional[Dict]:
        """Handle credential-based login"""
        payload = message.get("payload", {})
        username = payload.get("username")
        password = payload.get("password")
        trace_id = message.get("trace_id")

        if not username or not password:
            await self._send_error(websocket, "Username and password required", "CREDENTIALS_MISSING")
            return None

        # Check brute force
        if not await self._check_brute_force(username):
            logger.warning(f"Login blocked for user {username} due to too many failed attempts")
            await self._send_error(websocket, "Too many login attempts. Try again in 5 minutes.", "RATE_LIMITED")
            return None

        user = self.user_store.get_user_by_username(username)
        if user and user.is_active and user.verify_password(password):
            await self._record_attempt(username, True)
            self.user_store.update_last_login(user.user_id)

            token = jwt_handler.create_access_token(user.user_id, user.username, user.role)

            # Send token back
            await websocket.send(json.dumps({
                "type": Events.AUTH_TOKEN,
                "trace_id": trace_id,
                "payload": {
                    "access_token": token,
                    "expires_in": jwt_handler.expire_minutes * 60,
                    "user": user.to_dict()
                }
            }))

            # Also consider the current connection authenticated
            return {
                "sub": user.user_id,
                "username": user.username,
                "role": user.role,
                "type": "access"
            }
        else:
            await self._record_attempt(username, False)
            logger.warning(f"Failed login attempt for user: {username}")
            await self._send_error(websocket, "Invalid username or password", "INVALID_CREDENTIALS")
            return None

    async def _handle_token_auth(self, websocket, message: Dict) -> Optional[Dict]:
        """Handle token-based authentication"""
        token = message.get("payload", {}).get("token")
        trace_id = message.get("trace_id")

        if not token:
            await self._send_error(websocket, "Token missing", "TOKEN_MISSING")
            return None

        try:
            payload = jwt_handler.verify_token(token)

            # Success response
            await websocket.send(json.dumps({
                "type": Events.AUTH_SUCCESS,
                "trace_id": trace_id,
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
