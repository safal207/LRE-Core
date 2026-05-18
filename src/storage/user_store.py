"""
User storage
SQLite-based user persistence
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
from src.auth.models import User
from config.settings import settings


class UserStore:
    """User persistence layer"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize user store

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or settings.database.users_db_path
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """Create data directory if it doesn't exist"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Read migration file
            migration_file = Path(__file__).parent.parent.parent / "migrations" / "001_create_users_table.sql"

            if migration_file.exists():
                migration_sql = migration_file.read_text()
                conn.executescript(migration_sql)
            else:
                # Fallback inline schema
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash BLOB NOT NULL,
                        role TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        last_login REAL,
                        is_active BOOLEAN DEFAULT 1,
                        CHECK(role IN ('admin', 'developer', 'viewer'))
                    )
                """)

                conn.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_username
                    ON users(username)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_role
                    ON users(role)
                """)

            conn.commit()

    def create_user(self, user: User) -> None:
        """
        Create new user

        Args:
            user: User instance

        Raises:
            ValueError: If username already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO users (
                        user_id, username, password_hash, role,
                        created_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id,
                    user.username,
                    user.password_hash,
                    user.role,
                    user.created_at.timestamp(),
                    user.is_active
                ))
                conn.commit()
        except sqlite3.IntegrityError as e:
            if "username" in str(e).lower():
                raise ValueError(f"Username '{user.username}' already exists")
            raise

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: Username to search for

        Returns:
            User instance or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM users WHERE username = ?
            """, (username,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_user(row)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User instance or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_user(row)

    def update_last_login(self, user_id: str) -> None:
        """
        Update user's last login timestamp

        Args:
            user_id: User ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users
                SET last_login = ?
                WHERE user_id = ?
            """, (datetime.now(timezone.utc).timestamp(), user_id))
            conn.commit()

    def list_users(self, include_inactive: bool = False) -> List[User]:
        """
        List all users

        Args:
            include_inactive: Include inactive users

        Returns:
            List of User instances
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if include_inactive:
                cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            else:
                cursor = conn.execute("""
                    SELECT * FROM users
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """)

            return [self._row_to_user(row) for row in cursor.fetchall()]

    def deactivate_user(self, user_id: str) -> None:
        """
        Deactivate user

        Args:
            user_id: User ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users
                SET is_active = 0
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()

    def update_password(self, user_id: str, password_hash: bytes) -> None:
        """
        Update user's password hash

        Args:
            user_id: User ID
            password_hash: New password hash
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users
                SET password_hash = ?
                WHERE user_id = ?
            """, (password_hash, user_id))
            conn.commit()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User instance"""
        # created_at and last_login are stored as timestamps (REAL)
        created_at = datetime.fromtimestamp(row["created_at"], tz=timezone.utc)
        last_login = None
        if row["last_login"]:
            last_login = datetime.fromtimestamp(row["last_login"], tz=timezone.utc)

        return User(
            user_id=row["user_id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=created_at,
            last_login=last_login,
            is_active=bool(row["is_active"])
        )


# Global user store instance
user_store = UserStore()
