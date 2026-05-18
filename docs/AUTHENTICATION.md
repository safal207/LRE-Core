# LRE-Core Authentication System

This document describes the authentication and authorization system for LRE-Core.

## Overview

LRE-Core uses JWT (JSON Web Tokens) for WebSocket connection authentication and RBAC (Role-Based Access Control) for event-level authorization.

## Authentication Flow

LRE-Core supports two authentication flows:

### 1. Login Flow (Getting a Token)

Use this flow to exchange credentials (username/password) for a JWT token.

1.  **Connection**: Client opens a WebSocket connection.
2.  **Auth Login**: Client sends an `auth_login` message.
    ```json
    {
      "type": "auth_login",
      "trace_id": "login-trace-123",
      "timestamp": "2024-03-20T10:00:00Z",
      "payload": {
        "username": "your_username",
        "password": "your_password"
      }
    }
    ```
3.  **Response**:
    - **Success**: Server responds with `auth_token` containing the JWT and user info. The current connection is also considered authenticated.
    - **Failure**: Server responds with `auth_failure` and may close the connection.

### 2. Token Flow (Authenticate with existing Token)

Use this flow if you already have a valid JWT token.

1.  **Connection**: Client opens a WebSocket connection.
2.  **Auth Request**: Client sends an `auth_request` message.
    ```json
    {
      "type": "auth_request",
      "trace_id": "auth-trace-123",
      "timestamp": "2024-03-20T10:00:00Z",
      "payload": {
        "token": "YOUR_JWT_TOKEN"
      }
    }
    ```
3.  **Validation**: The server verifies the token.
    - If valid, server responds with `auth_success`.
    - If invalid, server responds with `auth_failure` and may close the connection.

4.  **Authorized Communication**: Once authenticated, the client can send other messages. Each message is checked against the user's role permissions.

## RBAC (Role-Based Access Control)

LRE-Core supports three roles:

| Role        | Description                                      | Permissions                                                                 |
| ----------- | ------------------------------------------------ | --------------------------------------------------------------------------- |
| `admin`     | Full system access                               | All events (`*`), including emergency shutdown and DB stats                 |
| `developer` | Development and monitoring                       | `get_agent_status`, `fetch_history`, `system_ping`, `echo_payload`          |
| `viewer`    | Read-only access                                 | `fetch_history`, `system_ping`                                              |

## Security Implementation

### Password Hashing
Passwords are never stored in plain text. We use **bcrypt** with a cost factor of 12 (configurable via `BCRYPT_COST_FACTOR`). The verification process includes dummy work on failure to mitigate timing attacks.

### Brute Force Protection
The server implements simple in-memory brute force protection. After 5 failed login attempts, the username is locked for 5 minutes.

### JWT Tokens
Tokens are signed using `HMAC-SHA256`. The `SECRET_KEY` must be at least 32 characters long. In production, always use a strong, randomly generated secret.

### Persistence
Users are stored in a dedicated SQLite database (`data/users.db`).

## Configuration

Settings are managed via environment variables (see `.env.example`):

- `JWT_SECRET_KEY`: Secret key for signing tokens (REQUIRED in production).
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 60).
- `BCRYPT_COST_FACTOR`: bcrypt hashing rounds (default: 12).
- `USERS_DB_PATH`: Path to the users database.

## CLI Management

Use the user management CLI to manage users:

```bash
# Create a new user
python3 -m src.cli.user_management create john_doe --role developer

# List users
python3 -m src.cli.user_management list

# Deactivate a user
python3 -m src.cli.user_management deactivate john_doe

# Change password
python3 -m src.cli.user_management change-password john_doe
```

## Security Best Practices

### Production Deployment

1. **Generate Strong Secret Key**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. **Set Environment Variables**:
   ```bash
   export JWT_SECRET_KEY="your-generated-secret"
   export ENVIRONMENT=production
   export REQUIRE_WSS=true
   ```
3. **Change Default Admin Password immediately after setup.**
4. **Always use WSS (WebSocket Secure)** in production to protect credentials and tokens in transit.

## Error Codes

- `E008`: Permission denied (RBAC violation).
- `AUTH_REQUIRED`: Authentication message expected but not received.
- `TOKEN_MISSING`: Token payload field missing.
- `INVALID_TOKEN`: Token is expired or signature is invalid.
