-- QDW Estate V1 — additive only. Never edit migrations 0001-0004.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS capability_requests (
  request_id TEXT PRIMARY KEY,
  capability TEXT NOT NULL,
  objective TEXT NOT NULL,
  request_json TEXT NOT NULL,
  request_hash TEXT NOT NULL UNIQUE,
  verification_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estate_resources (
  resource_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  version TEXT,
  descriptor_json TEXT NOT NULL,
  descriptor_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estate_resource_capabilities (
  resource_id TEXT NOT NULL REFERENCES estate_resources(resource_id) ON DELETE CASCADE,
  capability TEXT NOT NULL,
  PRIMARY KEY(resource_id, capability)
);
CREATE INDEX IF NOT EXISTS idx_estate_capability ON estate_resource_capabilities(capability,resource_id);

CREATE TABLE IF NOT EXISTS workflow_templates (
  template_id TEXT NOT NULL,
  version TEXT NOT NULL,
  template_json TEXT NOT NULL,
  template_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(template_id,version)
);

CREATE TABLE IF NOT EXISTS estate_route_decisions (
  route_decision_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES capability_requests(request_id),
  policy_id TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  candidate_snapshot_json TEXT NOT NULL,
  candidate_snapshot_hash TEXT NOT NULL,
  chosen_resource_id TEXT,
  reason_codes_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estate_context_packs (
  context_pack_id TEXT PRIMARY KEY,
  node_id TEXT,
  manifest_json TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  artifact_id TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estate_execution_episodes (
  episode_id TEXT PRIMARY KEY,
  graph_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  capability_request_id TEXT NOT NULL REFERENCES capability_requests(request_id),
  route_decision_id TEXT NOT NULL REFERENCES estate_route_decisions(route_decision_id),
  resource_id TEXT NOT NULL REFERENCES estate_resources(resource_id),
  executor_config_hash TEXT,
  context_pack_id TEXT REFERENCES estate_context_packs(context_pack_id),
  sandbox_id TEXT,
  status TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  wall_ms INTEGER,
  model_cost_usd REAL NOT NULL DEFAULT 0,
  tool_cost_usd REAL NOT NULL DEFAULT 0,
  compute_cost_usd REAL NOT NULL DEFAULT 0,
  human_cost_usd REAL NOT NULL DEFAULT 0,
  output_hash TEXT,
  failure_class TEXT,
  trace_artifact_id TEXT,
  verification_certificate_id TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(node_id,attempt_number)
);
CREATE INDEX IF NOT EXISTS idx_episode_status ON estate_execution_episodes(status,created_at);

CREATE TABLE IF NOT EXISTS estate_verification_requests (
  verification_request_id TEXT PRIMARY KEY,
  node_id TEXT NOT NULL,
  episode_id TEXT NOT NULL REFERENCES estate_execution_episodes(episode_id),
  policy_id TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  status TEXT NOT NULL,
  lease_owner TEXT,
  lease_until TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS estate_verification_results (
  verification_result_id TEXT PRIMARY KEY,
  verification_request_id TEXT NOT NULL REFERENCES estate_verification_requests(verification_request_id),
  gate_id TEXT NOT NULL,
  verifier_resource_id TEXT,
  passed INTEGER NOT NULL,
  receipt_artifact_id TEXT,
  detail_json TEXT NOT NULL,
  result_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estate_verification_certificates (
  verification_certificate_id TEXT PRIMARY KEY,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  certificate_json TEXT NOT NULL,
  certificate_hash TEXT NOT NULL,
  issued_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estate_resource_profiles (
  resource_id TEXT NOT NULL REFERENCES estate_resources(resource_id),
  capability TEXT NOT NULL,
  sample_count INTEGER NOT NULL DEFAULT 0,
  verified_success_count INTEGER NOT NULL DEFAULT 0,
  success_alpha REAL NOT NULL DEFAULT 1,
  success_beta REAL NOT NULL DEFAULT 1,
  mean_cost_usd REAL,
  mean_wall_ms REAL,
  failure_distribution_json TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT NOT NULL,
  PRIMARY KEY(resource_id,capability)
);

CREATE TABLE IF NOT EXISTS estate_components (
  component_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  canonical_repo TEXT,
  status TEXT NOT NULL,
  manifest_json TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estate_dependencies (
  consumer_component_id TEXT NOT NULL REFERENCES estate_components(component_id),
  provider_component_id TEXT NOT NULL REFERENCES estate_components(component_id),
  capability TEXT NOT NULL,
  required INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY(consumer_component_id,provider_component_id,capability)
);
