-- 0004_rights_and_resolution: requirements, fulfillments, human submissions, data grants

CREATE TABLE IF NOT EXISTS requirements (
    requirement_id TEXT PRIMARY KEY,
    requester_type TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    requirement_type_term_id TEXT NOT NULL,
    spec_json TEXT NOT NULL DEFAULT '{}',
    acceptance_spec_hash TEXT DEFAULT '',
    max_cost_usd REAL NOT NULL DEFAULT 0.0,
    deadline TEXT NOT NULL DEFAULT '',
    space_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_req_space ON requirements(space_id);
CREATE INDEX IF NOT EXISTS idx_req_status ON requirements(status);

CREATE TABLE IF NOT EXISTS fulfillments (
    fulfillment_id TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    estimated_cost REAL NOT NULL DEFAULT 0.0,
    expected_success REAL NOT NULL DEFAULT 0.0,
    expected_evidence_quality REAL NOT NULL DEFAULT 0.0,
    selected_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TEXT NOT NULL,
    FOREIGN KEY (requirement_id) REFERENCES requirements(requirement_id)
);

CREATE TABLE IF NOT EXISTS human_submissions (
    submission_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL,
    contributor_entity_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    artifact_ref TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'submitted',
    verification_receipt_id TEXT DEFAULT '',
    observation_id TEXT DEFAULT '',
    claim_id TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_hsub_status ON human_submissions(status);

CREATE TABLE IF NOT EXISTS data_grants (
    grant_id TEXT PRIMARY KEY,
    owner_entity_id TEXT NOT NULL,
    source_space_id TEXT NOT NULL,
    grantee_entity_id TEXT NOT NULL,
    purpose_term_id TEXT NOT NULL,
    scope_json TEXT NOT NULL DEFAULT '{}',
    allowed_operations_json TEXT NOT NULL DEFAULT '[]',
    raw_access INTEGER NOT NULL DEFAULT 0,
    training_allowed INTEGER NOT NULL DEFAULT 0,
    redistribution_allowed INTEGER NOT NULL DEFAULT 0,
    valid_from TEXT NOT NULL,
    valid_until TEXT NOT NULL DEFAULT '',
    revoked_at TEXT NOT NULL DEFAULT '',
    rights_backend TEXT NOT NULL DEFAULT 'native_local',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grant_owner ON data_grants(owner_entity_id);
CREATE INDEX IF NOT EXISTS idx_grant_grantee ON data_grants(grantee_entity_id);
