-- 0001_init: bounty engine tables

CREATE TABLE IF NOT EXISTS bounty_definitions (
    bounty_id TEXT PRIMARY KEY,
    bounty_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requirement TEXT NOT NULL,
    budget_usd REAL NOT NULL,
    deadline_seconds INTEGER NOT NULL,
    submission_format_json TEXT NOT NULL DEFAULT '{}',
    verification_commands_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bounty_submissions (
    submission_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    solver_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    content_json TEXT NOT NULL DEFAULT '{}',
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    submitted_at TEXT NOT NULL,
    FOREIGN KEY (bounty_id) REFERENCES bounty_definitions(bounty_id)
);

CREATE TABLE IF NOT EXISTS bounty_rewards (
    reward_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    submission_id TEXT NOT NULL,
    solver_id TEXT NOT NULL,
    amount_usd REAL NOT NULL,
    paid_at TEXT NOT NULL,
    FOREIGN KEY (bounty_id) REFERENCES bounty_definitions(bounty_id),
    FOREIGN KEY (submission_id) REFERENCES bounty_submissions(submission_id)
);

CREATE TABLE IF NOT EXISTS bounty_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    expected_cost_usd REAL NOT NULL,
    confidence REAL NOT NULL,
    time_seconds INTEGER NOT NULL,
    evidence_quality REAL NOT NULL,
    rights_clearance TEXT NOT NULL DEFAULT 'unknown',
    risk REAL NOT NULL DEFAULT 0.0,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (bounty_id) REFERENCES bounty_definitions(bounty_id)
);

CREATE TABLE IF NOT EXISTS bounty_gates (
    gate_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    gate_type TEXT NOT NULL,
    command TEXT NOT NULL,
    expected_exit_code INTEGER NOT NULL DEFAULT 0,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    FOREIGN KEY (bounty_id) REFERENCES bounty_definitions(bounty_id)
);

CREATE TABLE IF NOT EXISTS bounty_certificates (
    certificate_id TEXT PRIMARY KEY,
    bounty_id TEXT NOT NULL,
    submission_id TEXT NOT NULL DEFAULT '',
    artifact_hashes_json TEXT NOT NULL DEFAULT '[]',
    gate_hashes_json TEXT NOT NULL DEFAULT '[]',
    ledger_root TEXT NOT NULL DEFAULT '',
    source_commit TEXT NOT NULL DEFAULT '',
    issued_at TEXT NOT NULL
);
