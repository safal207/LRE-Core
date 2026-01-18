# LRE-Core Authentication System

This document describes the authentication and authorization system for LRE-Core.

## Overview

LRE-Core uses JWT (JSON Web Tokens) for WebSocket connection authentication and RBAC (Role-Based Access Control) for event-level authorization.

## Authentication Flow

1.  **Connection**: Client opens a WebSocket connection.
2.  **Auth Request**: Client MUST send an `auth_request` message as the very first message.
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
Passwords are never stored in plain text. We use **bcrypt** with a cost factor of 12 (configurable via `BCRYPT_COST_FACTOR`).

### JWT Tokens
Tokens are signed using `HMAC-SHA256`. The `SECRET_KEY` must be at least 32 characters long.

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
```

## Error Codes

- `E008`: Permission denied (RBAC violation).
- `AUTH_REQUIRED`: Authentication message expected but not received.
- `TOKEN_MISSING`: Token payload field missing.
- `INVALID_TOKEN`: Token is expired or signature is invalid.
