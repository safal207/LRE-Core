"""
Tests for User model
"""
import pytest
from src.auth.models import User, ROLE_PERMISSIONS

def test_user_creation():
    username = "test_user"
    password = "password123"
    role = "developer"

    user = User.create(username, password, role)

    assert user.username == username
    assert user.role == role
    assert user.is_active is True
    assert user.verify_password(password) is True
    assert user.verify_password("wrong_password") is False

def test_invalid_role():
    with pytest.raises(ValueError, match="Invalid role"):
        User.create("user", "password123", role="invalid_role")

def test_short_password():
    with pytest.raises(ValueError, match="at least 8 characters"):
        User.create("user", "short")

def test_user_to_dict():
    user = User.create("test_user", "password123", "viewer")
    d = user.to_dict()

    assert d["username"] == "test_user"
    assert d["role"] == "viewer"
    assert "password_hash" not in d
