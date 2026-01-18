-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'developer', 'viewer')),
    created_at REAL NOT NULL,
    last_login REAL,
    is_active BOOLEAN DEFAULT 1
);

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_active ON users(is_active);

-- Insert default admin user
-- Password: admin123 (CHANGE THIS IN PRODUCTION!)
INSERT OR IGNORE INTO users (user_id, username, password_hash, role, created_at, is_active)
VALUES (
    'user_default_admin',
    'admin',
    X'243262243132246e6b6c4d6e474d4f367a58456975656e6c6a59642e38744b644a644c5a4a78764475304651766f746645776156536136366d',
    'admin',
    strftime('%s', 'now'),
    1
);
