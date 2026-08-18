CREATE TABLE IF NOT EXISTS report_definitions(
  report_type TEXT NOT NULL,
  version TEXT NOT NULL,
  query_spec_json TEXT NOT NULL,
  output_schema_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(report_type,version)
);
CREATE TABLE IF NOT EXISTS report_runs(
  report_run_id TEXT PRIMARY KEY,
  report_type TEXT NOT NULL,
  report_version TEXT NOT NULL,
  space_id TEXT NOT NULL,
  period_start TEXT,
  period_end TEXT,
  input_snapshot_hash TEXT NOT NULL,
  output_artifact_hash TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS share_packages(
  share_id TEXT PRIMARY KEY,
  source_space_id TEXT NOT NULL,
  audience_type TEXT NOT NULL,
  policy_snapshot_hash TEXT NOT NULL,
  selection_spec_json TEXT NOT NULL,
  artifact_hash TEXT,
  expires_at TEXT,
  revoked_at TEXT,
  created_at TEXT NOT NULL
);
