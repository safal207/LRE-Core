"""
Secrets management helper
Provides access to sensitive configuration
"""
from config.settings import settings

def get_jwt_secret() -> str:
    """Get the JWT secret key"""
    return settings.auth.secret_key

def get_bcrypt_rounds() -> int:
    """Get the bcrypt cost factor"""
    return settings.auth.bcrypt_cost_factor
