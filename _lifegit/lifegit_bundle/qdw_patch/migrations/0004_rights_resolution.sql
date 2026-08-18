CREATE TABLE IF NOT EXISTS requirements(
  requirement_id TEXT PRIMARY KEY,
  requester_type TEXT NOT NULL,
  requester_id TEXT NOT NULL,
  requirement_type_term_id TEXT NOT NULL,
  spec_json TEXT NOT NULL,
  acceptance_spec_hash TEXT,
  max_cost_usd REAL,
  deadline TEXT,
  space_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fulfillments(
  fulfillment_id TEXT PRIMARY KEY,
  requirement_id TEXT NOT NULL,
  provider_type TEXT NOT NULL,
  provider_id TEXT,
  estimated_cost_usd REAL,
  expected_success REAL,
  expected_evidence_quality REAL,
  selected_at TEXT,
  status TEXT NOT NULL DEFAULT 'CANDIDATE'
);
CREATE TABLE IF NOT EXISTS human_submissions(
  submission_id TEXT PRIMARY KEY,
  action_id TEXT NOT NULL,
  contributor_entity_id TEXT,
  submitted_at TEXT NOT NULL,
  artifact_ref TEXT,
  status TEXT NOT NULL DEFAULT 'SUBMITTED',
  verification_receipt_id TEXT
);
CREATE TABLE IF NOT EXISTS data_grants(
  grant_id TEXT PRIMARY KEY,
  owner_entity_id TEXT NOT NULL,
  source_space_id TEXT NOT NULL,
  grantee_entity_id TEXT,
  purpose_term_id TEXT NOT NULL,
  scope_json TEXT NOT NULL,
  allowed_operations_json TEXT NOT NULL,
  raw_access INTEGER NOT NULL DEFAULT 0,
  training_allowed INTEGER NOT NULL DEFAULT 0,
  redistribution_allowed INTEGER NOT NULL DEFAULT 0,
  valid_from TEXT,
  valid_until TEXT,
  revoked_at TEXT,
  rights_backend TEXT NOT NULL DEFAULT 'native',
  created_at TEXT NOT NULL
);
