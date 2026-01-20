# Liminal Transport Protocol (LTP) Events

This document lists canonical event types used in Liminal Runtime.

## System Events

### `system_ping`
- **Direction**: INBOUND
- **Description**: Health check initiated by client.
- **Payload**: `{ "agent_id": "string" }`

### `system_pong`
- **Direction**: OUTBOUND
- **Description**: Server response to ping.
- **Payload**: `{ "server_timestamp": "string" }`

## User Events

### `echo_payload`
- **Direction**: BIDIRECTIONAL
- **Description**: Debug action that echoes the input payload.
- **Payload**: User-defined object.

## Storage & History Events

### `fetch_history`
- **Direction**: INBOUND
- **Description**: Request event history from the persistence layer.
- **Payload**:
  - `limit` (int, optional): Max events to return.
  - `trace_id` (string, optional): Filter by session.
  - `agent_id` (string, optional): Filter by agent.
  - `type` (string, optional): Filter by event type.

### `history_result`
- **Direction**: OUTBOUND
- **Description**: Response to `fetch_history`.
- **Payload**:
  - `events` (array): List of event objects.
  - `count` (int): Total events in DB.
  - `filters` (object): Filters applied to the query.

### `get_agent_status`
- **Direction**: INBOUND
- **Description**: Get list of recently active agents.
- **Payload**: `{ "since_seconds": int }`

### `agent_status_result`
- **Direction**: OUTBOUND
- **Description**: List of active agents and their status.

### `get_db_stats`
- **Direction**: INBOUND
- **Description**: Request database statistics.

### `db_stats_result`
- **Direction**: OUTBOUND
- **Description**: Database metrics (total events, unique traces, etc.).

## Control Events

### `emergency_shutdown`
- **Direction**: INBOUND
- **Description**: Initiates emergency shutdown.
- **Payload**: `{ "reason": "string", "admin_id": "string" }`
