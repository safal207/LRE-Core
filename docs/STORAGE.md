# Storage Layer Documentation

## Security

### SQL Injection Protection

All database queries use **parameterized queries** to prevent SQL injection attacks.

❌ **NEVER do this:**
```python
# VULNERABLE - allows SQL injection
sql = f"SELECT * FROM users WHERE name='{user_input}'"
```

✅ **ALWAYS do this:**
```python
# SAFE - uses parameterized query
sql = "SELECT * FROM users WHERE name=?"
cursor.execute(sql, (user_input,))
```

### Concurrency Safety

State updates are **atomic** using database transactions:

```python
# This is thread-safe
state_manager.update_state('trace-123', {'counter': count + 1})
```

The implementation uses `BEGIN IMMEDIATE` to lock the database during read-modify-write operations.

## Connection Management

Connections are **pooled per thread**:

- Each thread gets its own connection
- Connections are reused within threads
- No connection leaks under normal operation

```python
# Connections are automatically managed
backend = SQLiteBackend('data/lre.db')
conn = backend.get_connection()  # Reuses connection if exists

# Cleanup when thread exits
backend.close_connection()
```

## Performance Considerations

### Query Optimization

For frequently accessed data, ensure proper indexes exist:

```sql
-- Index for filtering by event type
CREATE INDEX idx_messages_type ON messages(type);

-- Composite index for trace + type queries
CREATE INDEX idx_messages_trace_type ON messages(trace_id, type);
```

### Transaction Best Practices

- Keep transactions short
- Use `BEGIN IMMEDIATE` for write transactions
- Always commit or rollback explicitly

```python
try:
    cursor.execute("BEGIN IMMEDIATE")
    # ... do work ...
    conn.commit()
except:
    conn.rollback()
    raise
```
