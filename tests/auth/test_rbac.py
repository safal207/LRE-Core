"""
Tests for RBAC
"""
from src.auth.rbac import check_permission

def test_admin_permissions():
    # Admin should have all permissions
    assert check_permission("admin", "any_event") is True
    assert check_permission("admin", "emergency_shutdown") is True

def test_developer_permissions():
    assert check_permission("developer", "get_agent_status") is True
    assert check_permission("developer", "fetch_history") is True
    assert check_permission("developer", "emergency_shutdown") is False

def test_viewer_permissions():
    assert check_permission("viewer", "fetch_history") is True
    assert check_permission("viewer", "system_ping") is True
    assert check_permission("viewer", "get_agent_status") is False

def test_invalid_role_permissions():
    assert check_permission("non_existent_role", "system_ping") is False
