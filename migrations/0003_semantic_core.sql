-- 0003_semantic_core: ontology, spaces, edges, events, states, semantic objects, tensions, threads

CREATE TABLE IF NOT EXISTS ontology_terms (
    term_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    canonical_key TEXT NOT NULL,
    label TEXT NOT NULL,
    parent_term_id TEXT DEFAULT '',
    schema_version TEXT NOT NULL DEFAULT '1.0',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    UNIQUE(kind, canonical_key)
);

CREATE TABLE IF NOT EXISTS spaces (
    space_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    owner_entity_id TEXT DEFAULT '',
    default_visibility TEXT NOT NULL DEFAULT 'private',
    policy_id TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS object_edges (
    edge_id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    predicate_term_id TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    supporting_claim_id TEXT DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edges_subject ON object_edges(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_edges_object ON object_edges(object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_edges_predicate ON object_edges(predicate_term_id);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    event_type_term_id TEXT NOT NULL,
    subject_entity_id TEXT NOT NULL,
    object_entity_id TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    ended_at TEXT DEFAULT '',
    attributes_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_space ON events(space_id);
CREATE INDEX IF NOT EXISTS idx_events_subject ON events(subject_entity_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type_term_id);

CREATE TABLE IF NOT EXISTS states (
    state_id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    subject_entity_id TEXT NOT NULL,
    dimension_term_id TEXT NOT NULL,
    value_json TEXT NOT NULL DEFAULT '{}',
    valid_from TEXT NOT NULL,
    valid_until TEXT DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_states_space ON states(space_id);
CREATE INDEX IF NOT EXISTS idx_states_subject ON states(subject_entity_id);

CREATE TABLE IF NOT EXISTS semantic_objects (
    object_id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    object_type_term_id TEXT NOT NULL,
    subject_entity_id TEXT DEFAULT '',
    canonical_key TEXT NOT NULL,
    content_json TEXT NOT NULL DEFAULT '{}',
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semo_space ON semantic_objects(space_id);
CREATE INDEX IF NOT EXISTS idx_semo_type ON semantic_objects(object_type_term_id);
CREATE INDEX IF NOT EXISTS idx_semo_status ON semantic_objects(status);

CREATE TABLE IF NOT EXISTS tensions (
    tension_id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    subject_segment TEXT NOT NULL,
    dimension TEXT NOT NULL,
    observed_state_concept TEXT NOT NULL,
    desired_state_concept TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    prevalence REAL NOT NULL DEFAULT 0.0,
    recurrence REAL NOT NULL DEFAULT 0.0,
    severity REAL NOT NULL DEFAULT 0.0,
    persistence REAL NOT NULL DEFAULT 0.0,
    confidence REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tensions_space ON tensions(space_id);
CREATE INDEX IF NOT EXISTS idx_tensions_dimension ON tensions(dimension);

CREATE TABLE IF NOT EXISTS threads (
    thread_id TEXT PRIMARY KEY,
    space_id TEXT NOT NULL,
    thread_type_term_id TEXT NOT NULL,
    primary_subject_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_threads_space ON threads(space_id);

CREATE TABLE IF NOT EXISTS thread_members (
    thread_id TEXT NOT NULL,
    member_type TEXT NOT NULL,
    member_id TEXT NOT NULL,
    role_term_id TEXT NOT NULL DEFAULT '',
    ordinal INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (thread_id, member_type, member_id)
);
