-- 0005_reports: report definitions, report runs, share packages

CREATE TABLE IF NOT EXISTS report_definitions (
    report_type TEXT NOT NULL,
    version TEXT NOT NULL,
    query_spec_json TEXT NOT NULL DEFAULT '{}',
    schema_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    PRIMARY KEY (report_type, version)
);

CREATE TABLE IF NOT EXISTS report_runs (
    report_run_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    report_version TEXT NOT NULL DEFAULT '',
    space_id TEXT NOT NULL,
    period_start TEXT NOT NULL DEFAULT '',
    period_end TEXT NOT NULL DEFAULT '',
    input_snapshot_hash TEXT NOT NULL DEFAULT '',
    output_artifact_hash TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rreport_space ON report_runs(space_id);
CREATE INDEX IF NOT EXISTS idx_rreport_type ON report_runs(report_type);

CREATE TABLE IF NOT EXISTS share_packages (
    share_id TEXT PRIMARY KEY,
    source_space_id TEXT NOT NULL,
    audience_type TEXT NOT NULL,
    policy_snapshot_hash TEXT NOT NULL DEFAULT '',
    selection_spec_json TEXT NOT NULL DEFAULT '{}',
    artifact_hash TEXT NOT NULL DEFAULT '',
    expires_at TEXT NOT NULL DEFAULT '',
    revoked_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_share_source ON share_packages(source_space_id);
