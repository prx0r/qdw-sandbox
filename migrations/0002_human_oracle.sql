-- 0002_human_oracle: worker profiles and human routes

CREATE TABLE IF NOT EXISTS worker_profiles (
    worker_id TEXT PRIMARY KEY,
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    reputation REAL NOT NULL DEFAULT 0.5,
    completion_rate REAL NOT NULL DEFAULT 0.0,
    total_tasks INTEGER NOT NULL DEFAULT 0,
    avg_quality REAL NOT NULL DEFAULT 0.0,
    identity_verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_routes (
    route_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    cost_per_hour_usd REAL NOT NULL,
    reliability REAL NOT NULL,
    latency_seconds INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (worker_id) REFERENCES worker_profiles(worker_id)
);

CREATE TABLE IF NOT EXISTS human_task_log (
    task_log_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    logged_at TEXT NOT NULL
);
