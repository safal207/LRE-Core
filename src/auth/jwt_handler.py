"""
JWT token handler
Handles creation and verification of JWT tokens
"""
import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from config.settings import settings


class JWTHandler:
    """JWT token management"""

    def __init__(self):
        self.secret_key = settings.auth.secret_key
        self.algorithm = settings.auth.algorithm
        self.expire_minutes = settings.auth.access_token_expire_minutes

    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User ID
            username: Username
            role: User role
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.expire_minutes
            )

        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")

            return payload

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def decode_token_unsafe(self, token: str) -> Optional[Dict]:
        """
        Decode token without verification (for debugging only)

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None


# Global JWT handler instance
jwt_handler = JWTHandler()
