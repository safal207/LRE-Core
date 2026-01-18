"""
Tests for UserStore
"""
import pytest
import os
from src.storage.user_store import UserStore
from src.auth.models import User

@pytest.fixture
def temp_db():
    db_path = "data/test_users.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    store = UserStore(db_path=db_path)
    yield store

    if os.path.exists(db_path):
        os.remove(db_path)

def test_create_and_get_user(temp_db):
    user = User.create("test_user", "password123", "developer")
    temp_db.create_user(user)

    retrieved = temp_db.get_user_by_username("test_user")
    assert retrieved is not None
    assert retrieved.username == "test_user"
    assert retrieved.role == "developer"
    assert retrieved.verify_password("password123") is True

def test_duplicate_username(temp_db):
    user1 = User.create("test_user", "password123", "viewer")
    temp_db.create_user(user1)

    user2 = User.create("test_user", "different_pass", "admin")
    with pytest.raises(ValueError, match="already exists"):
        temp_db.create_user(user2)

def test_list_users(temp_db):
    temp_db.create_user(User.create("user1", "pass12345", "viewer"))
    temp_db.create_user(User.create("user2", "pass12345", "developer"))

    users = temp_db.list_users()
    # Including default admin if migration ran
    usernames = [u.username for u in users]
    assert "user1" in usernames
    assert "user2" in usernames

def test_deactivate_user(temp_db):
    user = User.create("deactive_me", "pass12345", "viewer")
    temp_db.create_user(user)

    temp_db.deactivate_user(user.user_id)

    retrieved = temp_db.get_user_by_username("deactive_me")
    assert retrieved.is_active is False

    # Should not be in active list
    active_users = temp_db.list_users(include_inactive=False)
    assert "deactive_me" not in [u.username for u in active_users]
