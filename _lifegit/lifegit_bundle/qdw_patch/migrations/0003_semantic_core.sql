-- QDW proposed semantic core for LifeGit / reality sensing.
CREATE TABLE IF NOT EXISTS spaces(
  space_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  owner_entity_id TEXT,
  label TEXT NOT NULL,
  default_visibility TEXT NOT NULL DEFAULT 'PRIVATE',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ontology_terms(
  term_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  canonical_key TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  parent_term_id TEXT,
  schema_version TEXT NOT NULL DEFAULT '1.0.0',
  status TEXT NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS semantic_objects(
  object_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  object_type_term_id TEXT NOT NULL,
  subject_entity_id TEXT,
  canonical_key TEXT,
  content_json TEXT NOT NULL,
  first_observed_at TEXT,
  last_observed_at TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS temporal_events(
  event_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  event_type_term_id TEXT NOT NULL,
  subject_entity_id TEXT,
  object_entity_id TEXT,
  started_at TEXT,
  ended_at TEXT,
  attributes_json TEXT NOT NULL DEFAULT '{}',
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS states(
  state_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  subject_entity_id TEXT NOT NULL,
  dimension_term_id TEXT NOT NULL,
  value_json TEXT NOT NULL,
  valid_from TEXT,
  valid_until TEXT,
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tensions(
  tension_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  tension_type_term_id TEXT NOT NULL,
  subject_entity_id TEXT,
  observed_state_json TEXT NOT NULL,
  desired_state_json TEXT,
  prevalence REAL,
  recurrence REAL,
  severity REAL,
  persistence REAL,
  confidence REAL NOT NULL DEFAULT 0.5,
  first_observed_at TEXT,
  last_observed_at TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS object_edges(
  edge_id TEXT PRIMARY KEY,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  predicate_term_id TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  supporting_claim_id TEXT,
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_links(
  evidence_link_id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  evidence_id TEXT NOT NULL,
  role_term_id TEXT,
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS threads(
  thread_id TEXT PRIMARY KEY,
  space_id TEXT NOT NULL,
  thread_type_term_id TEXT NOT NULL,
  primary_subject_id TEXT,
  started_at TEXT,
  ended_at TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  confidence REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS thread_members(
  thread_id TEXT NOT NULL,
  member_type TEXT NOT NULL,
  member_id TEXT NOT NULL,
  role_term_id TEXT,
  ordinal INTEGER,
  PRIMARY KEY(thread_id,member_type,member_id)
);
