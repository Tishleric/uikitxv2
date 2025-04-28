CREATE TABLE IF NOT EXISTS trace_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT    NOT NULL,
    log_type     TEXT    NOT NULL,
    name         TEXT    NOT NULL,
    duration_ms  REAL,
    payload_json TEXT    -- JSON string
);
