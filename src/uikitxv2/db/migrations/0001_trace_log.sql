CREATE TABLE IF NOT EXISTS TraceLog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    seq INTEGER NOT NULL,
    func TEXT NOT NULL,
    wall_ms REAL,
    cpu_pct_start REAL,
    cpu_pct_end REAL,
    error TEXT
);
