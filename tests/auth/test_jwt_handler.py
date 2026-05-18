"""
Tests for JWT handler
"""
import pytest
from datetime import timedelta
from src.auth.jwt_handler import JWTHandler
from config.settings import settings

@pytest.fixture
def jwt_h():
    return JWTHandler()

def test_create_and_verify_token(jwt_h):
    user_id = "user_123"
    username = "test_user"
    role = "developer"

    token = jwt_h.create_access_token(user_id, username, role)
    assert isinstance(token, str)

    payload = jwt_h.verify_token(token)
    assert payload["sub"] == user_id
    assert payload["username"] == username
    assert payload["role"] == role
    assert payload["type"] == "access"

def test_expired_token(jwt_h):
    user_id = "user_123"
    username = "test_user"
    role = "developer"

    # Create token that expired 1 minute ago
    token = jwt_h.create_access_token(
        user_id, username, role,
        expires_delta=timedelta(minutes=-1)
    )

    with pytest.raises(ValueError, match="Token has expired"):
        jwt_h.verify_token(token)

def test_invalid_token(jwt_h):
    with pytest.raises(ValueError, match="Invalid token"):
        jwt_h.verify_token("invalid.token.here")
