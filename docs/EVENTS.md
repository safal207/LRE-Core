# Event Registry

This document is the **single source of truth** for all supported LTP event types.

## Event Specification Template

For each event:
- **Purpose**: What does this event do?
- **Direction**: Client→Server, Server→Client, or Bidirectional
- **Persistence**: Is it stored in database?
- **Response**: Expected response event (if any)
- **Payload Schema**: JSON schema for payload

---

## System Events

### system_ping

**Purpose**: Connection health check and latency measurement

**Direction**: Client → Server

**Persistence**: Yes

**Response**: `system_pong`

**Payload Schema**:
```json
{
  "client_timestamp": "2025-01-14T10:30:00.000Z"  // Optional
}
```

**Example**:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "system_ping",
  "timestamp": "2025-01-14T10:30:00.000Z",
  "payload": {
    "client_timestamp": "2025-01-14T10:30:00.000Z"
  }
}
```

---

### system_pong

**Purpose**: Response to system_ping

**Direction**: Server → Client

**Persistence**: Yes

**Response**: None

**Payload Schema**:
```json
{
  "server_timestamp": "2025-01-14T10:30:00.100Z",
  "latency_ms": 100  // Optional: calculated server-side
}
```

---

## User Events

### echo_payload

**Purpose**: Payload reflection test for protocol validation

**Direction**: Bidirectional

**Persistence**: Yes

**Response**: Same event with identical payload

**Payload Schema**:
```json
{
  // Any valid JSON object
}
```

**Example**:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "echo_payload",
  "timestamp": "2025-01-14T10:30:00.000Z",
  "payload": {
    "test_data": "hello world",
    "nested": {
      "value": 42
    }
  }
}
```

---

## Control Events

### emergency_shutdown

**Purpose**: Graceful system termination

**Direction**: Admin → Server

**Persistence**: Yes

**Response**: Connection closed with status code 1000

**Payload Schema**:
```json
{
  "reason": "string",      // Required: shutdown reason
  "admin_id": "string"     // Required: admin identifier
}
```

**Example**:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "emergency_shutdown",
  "timestamp": "2025-01-14T10:30:00.000Z",
  "payload": {
    "reason": "Maintenance window",
    "admin_id": "admin@liminal.dev"
  }
}
```

---

## Storage Events

### fetch_history

**Purpose**: Retrieve event log for a session, agent, or event type
**Direction**: Client → Server
**Persistence**: Yes (query operation)
**Response**: `history_result`

**Payload Schema**:
```json
{
  "trace_id": "uuid",      // Optional: filter by session
  "agent_id": "string",    // Optional: filter by agent
  "type": "event_type",    // Optional: filter by event type
  "limit": 100             // Optional: max events (default: 100)
}
```

**Example**:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "fetch_history",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "payload": {
    "agent_id": "agent_001",
    "limit": 50
  }
}
```

---

### history_result

**Purpose**: Response containing filtered event history
**Direction**: Server → Client
**Persistence**: Yes
**Response**: None

**Payload Schema**:
```json
{
  "events": [
    {
      "id": 123,
      "trace_id": "uuid",
      "type": "system_ping",
      "timestamp": "2025-01-15T10:30:00.000Z",
      "direction": "INBOUND",
      "payload": {},
      "created_at": 1705315800.123
    }
  ],
  "count": 1,
  "filters": {}
}
```

---

## Error Events

### error

**Purpose**: Protocol or runtime error notification

**Direction**: Server → Client

**Persistence**: Yes

**Response**: None

**Payload Schema**:
```json
{
  "code": "string",        // Error code (see PROTOCOL.md)
  "message": "string",     // Human-readable message
  "details": "string"      // Optional: additional context
}
```

---

## Adding New Events

To add a new event type:

1. Add constant to `src/core/events.py`
2. Document here with full specification
3. Implement handler in `src/transport/handler.py`
4. Add tests in `tests/`
5. Update CHANGELOG.md

---

## Event Statistics

| Category | Count |
|----------|-------|
| System   | 2     |
| User     | 1     |
| Control  | 1     |
| Storage  | 2     |
| Error    | 1     |
| **Total**| **7** |

---

## Version History

- **v1.0** (2025-01-14): Initial registry with core events
