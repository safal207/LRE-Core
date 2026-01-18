"""
Configuration management for LRE-Core
Loads settings from environment variables with validation
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Load .env file if exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed


@dataclass
class AuthSettings:
    """Authentication configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    bcrypt_cost_factor: int = 12
    require_wss: bool = False  # True in production

    def __post_init__(self):
        """Validate settings"""
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY must be set")

        if len(self.secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")

        if self.secret_key == "dev-only-insecure-key-change-in-prod":
            import warnings
            warnings.warn(
                "Using development secret key. NEVER use this in production!",
                UserWarning
            )

        if self.bcrypt_cost_factor < 10:
            raise ValueError("BCRYPT_COST_FACTOR must be at least 10")


@dataclass
class DatabaseSettings:
    """Database configuration"""
    users_db_path: str = "data/users.db"
    events_db_path: str = "data/lre_core.db"


@dataclass
class Settings:
    """Global application settings"""
    auth: AuthSettings
    database: DatabaseSettings
    environment: str = "development"
    debug: bool = False

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables"""
        # Get environment
        env = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"

        # Auth settings
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            if env == "production":
                raise RuntimeError("JWT_SECRET_KEY must be set in production")
            # Use insecure default for development
            secret_key = "dev-only-insecure-key-change-in-prod"

        auth = AuthSettings(
            secret_key=secret_key,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
            ),
            bcrypt_cost_factor=int(os.getenv("BCRYPT_COST_FACTOR", "12")),
            require_wss=os.getenv("REQUIRE_WSS", "false").lower() == "true"
        )

        # Database settings
        database = DatabaseSettings(
            users_db_path=os.getenv("USERS_DB_PATH", "data/users.db"),
            events_db_path=os.getenv("EVENTS_DB_PATH", "data/lre_core.db")
        )

        return cls(
            auth=auth,
            database=database,
            environment=env,
            debug=debug
        )


# Global settings instance
settings = Settings.load()
