"""
Role-Based Access Control (RBAC)
Manages permissions and access control
"""
import secrets
from typing import List
from src.auth.models import ROLE_PERMISSIONS


def check_permission(role: str, event_type: str) -> bool:
    """
    Check if role has permission for event type
    Uses constant-time comparison to prevent timing attacks

    Args:
        role: User role
        event_type: Event type to check

    Returns:
        True if role has permission, False otherwise
    """
    allowed_events = ROLE_PERMISSIONS.get(role, [])

    # Check for wildcard permission (admin)
    has_wildcard = any(
        secrets.compare_digest(perm, "*")
        for perm in allowed_events
    )

    if has_wildcard:
        return True

    # Check for specific permission
    # Use constant-time comparison for security
    has_permission = any(
        secrets.compare_digest(perm, event_type)
        for perm in allowed_events
    )

    return has_permission


def get_role_permissions(role: str) -> List[str]:
    """
    Get all permissions for a role

    Args:
        role: User role

    Returns:
        List of allowed event types
    """
    return ROLE_PERMISSIONS.get(role, []).copy()


def get_all_roles() -> List[str]:
    """Get list of all available roles"""
    return list(ROLE_PERMISSIONS.keys())
