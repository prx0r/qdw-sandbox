-- 0003_data_rights: licensing and rights backend

CREATE TABLE IF NOT EXISTS data_licences (
    licence_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    contributor_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    scope TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    operations_json TEXT NOT NULL DEFAULT '[]',
    raw_export INTEGER NOT NULL DEFAULT 0,
    training INTEGER NOT NULL DEFAULT 0,
    redistribution INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL DEFAULT '',
    price_usd REAL NOT NULL DEFAULT 0.0,
    rights_backend TEXT NOT NULL DEFAULT 'native_local',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_rights_log (
    log_id TEXT PRIMARY KEY,
    licence_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    granted INTEGER NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    checked_at TEXT NOT NULL,
    FOREIGN KEY (licence_id) REFERENCES data_licences(licence_id)
);
