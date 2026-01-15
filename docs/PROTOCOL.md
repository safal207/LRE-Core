# LTP (Liminal Transport Protocol) v1.0

## Overview
LTP is the communication protocol for Liminal Runtime Environment. It defines message structure, guarantees, and error handling.

## Message Envelope

Every message MUST conform to this JSON structure:

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "system_ping",
  "timestamp": "2025-01-14T10:30:00.000Z",
  "payload": {},
  "meta": {}
}
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trace_id` | UUID v4 | Yes | Immutable session identifier |
| `type` | String | Yes | Event type (must match EVENTS.md) |
| `timestamp` | ISO 8601 | Yes | UTC timestamp |
| `payload` | Object | No | Event-specific data |
| `meta` | Object | No | Optional metadata (routing, auth, etc.) |

### Constraints

- **trace_id**: Must remain constant for entire session lifecycle
- **type**: Must be registered in `EVENTS.md`
- **timestamp**: Must be in UTC timezone with millisecond precision
- **payload**: Max size 1MB (configurable via `LTP_MAX_PAYLOAD_SIZE` environment variable)

## Protocol Guarantees

1. **Immutability**: `trace_id` never changes during session
2. **Persistence**: All messages stored in SQLite with trace_id indexing
3. **Idempotency**: Duplicate messages with same trace_id are deduplicated
4. **Ordering**: Messages processed in arrival order per trace_id

## Error Codes

| Code | Category | Description | Client Action |
|------|----------|-------------|---------------|
| E001 | Protocol | Invalid JSON structure | Fix message format and retry |
| E002 | Protocol | Unknown event type | Check EVENTS.md registry |
| E003 | Auth | Unauthorized trace_id | Re-authenticate |
| E004 | Runtime | LRE execution failure | Retry with exponential backoff |
| E005 | Storage | Database write failed | Message queued for retry |
| E006 | Validation | Required field missing | Add missing fields |
| E007 | Validation | Field type mismatch | Correct field types |

## Error Response Format

```json
{
  "trace_id": "original-trace-id",
  "type": "error",
  "timestamp": "2025-01-14T10:30:00.000Z",
  "payload": {
    "code": "E001",
    "message": "Invalid JSON structure",
    "details": "Missing required field: trace_id"
  }
}
```

## Message Flow Example

```
Client                    Server                    Runtime
  |                         |                         |
  |--system_ping---------->|                         |
  |                         |--validate_message----->|
  |                         |<--validation_ok--------|
  |                         |--persist_to_db-------->|
  |                         |<--db_write_ok----------|
  |<--system_pong----------|                         |
  |                         |                         |
```

## Version History

- **v1.0** (2025-01-14): Initial specification

---

## Future Considerations

- Binary payload support (v2.0)
- Compression for large payloads
- Streaming events
- Priority queuing
