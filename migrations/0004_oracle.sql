-- 0004_oracle: resource allocation and stacking

CREATE TABLE IF NOT EXISTS resource_needs (
    need_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    required_capabilities_json TEXT NOT NULL DEFAULT '[]',
    budget_usd REAL NOT NULL,
    deadline_seconds INTEGER NOT NULL,
    quality_floor REAL NOT NULL DEFAULT 0.7,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resource_allocations (
    allocation_id TEXT PRIMARY KEY,
    need_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    expected_cost_usd REAL NOT NULL,
    expected_confidence REAL NOT NULL,
    expected_time_seconds INTEGER NOT NULL,
    reason_codes_json TEXT NOT NULL DEFAULT '[]',
    allocated_at TEXT NOT NULL,
    FOREIGN KEY (need_id) REFERENCES resource_needs(need_id)
);

CREATE TABLE IF NOT EXISTS allocation_outcomes (
    outcome_id TEXT PRIMARY KEY,
    allocation_id TEXT NOT NULL,
    actual_cost_usd REAL,
    actual_confidence REAL,
    success INTEGER,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (allocation_id) REFERENCES resource_allocations(allocation_id)
);
