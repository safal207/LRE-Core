"""
Authentication models
Defines User, Role and related data structures
"""
import bcrypt
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum


class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

    @property
    def permissions(self) -> List[str]:
        """Get permissions for role"""
        return ROLE_PERMISSIONS[self.value]


# Role-based permissions
ROLE_PERMISSIONS = {
    "admin": [
        "*",  # Wildcard - all permissions
        "emergency_shutdown",
        "get_db_stats",
        "get_agent_status",
        "fetch_history",
        "system_ping",
        "echo_payload"
    ],
    "developer": [
        "get_agent_status",
        "fetch_history",
        "system_ping",
        "echo_payload"
    ],
    "viewer": [
        "fetch_history",
        "system_ping"
    ]
}


@dataclass
class User:
    """User model"""
    user_id: str
    username: str
    password_hash: bytes
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        """Validate user data"""
        if self.role not in ROLE_PERMISSIONS:
            raise ValueError(f"Invalid role: {self.role}")

        if not isinstance(self.password_hash, bytes):
            raise TypeError("password_hash must be bytes")

    @staticmethod
    def hash_password(password: str, cost_factor: int = 12) -> bytes:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password
            cost_factor: bcrypt cost factor (default: 12)

        Returns:
            Password hash as bytes
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=cost_factor)
        )

    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash
            )
        except Exception:
            # Perform dummy work to mitigate timing attacks
            bcrypt.hashpw(b"dummy_password", bcrypt.gensalt(rounds=12))
            return False

    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        role: str = "viewer",
        cost_factor: int = 12
    ) -> "User":
        """
        Create new user with hashed password

        Args:
            username: Unique username
            password: Plain text password
            role: User role (admin, developer, viewer)
            cost_factor: bcrypt cost factor

        Returns:
            New User instance
        """
        # Validate username
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        # Generate unique user_id
        user_id = f"user_{secrets.token_hex(8)}"

        # Hash password
        password_hash = cls.hash_password(password, cost_factor)

        return cls(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(timezone.utc),
            is_active=True
        )

    def has_permission(self, event_type: str) -> bool:
        """
        Check if user has permission for event type

        Args:
            event_type: Event type to check

        Returns:
            True if user has permission, False otherwise
        """
        from src.auth.rbac import check_permission
        return check_permission(self.role, event_type)

    def to_dict(self) -> dict:
        """Convert user to dictionary (without password_hash)"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
