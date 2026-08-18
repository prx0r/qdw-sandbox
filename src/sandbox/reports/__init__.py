"""Reports module — report definitions, runs, share packages."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import ReportDefinition, ReportRun, SharePackage, new_id, utc_now


class ReportRegistry:
    def __init__(self, db: Database):
        self.db = db

    def define_report(self, report_type: str, version: str,
                      query_spec: dict[str, Any] | None = None,
                      schema: dict[str, Any] | None = None) -> ReportDefinition:
        defn = ReportDefinition(report_type=report_type, version=version,
                                query_spec=query_spec or {}, schema=schema or {})
        with self.db.tx() as con:
            con.execute(
                """INSERT OR REPLACE INTO report_definitions
                   (report_type, version, query_spec_json, schema_json, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (defn.report_type, defn.version, json.dumps(defn.query_spec),
                 json.dumps(defn.schema), defn.created_at),
            )
        return defn

    def run_report(self, report_type: str, space_id: str,
                   period_start: str = "", period_end: str = "") -> ReportRun:
        run = ReportRun(
            report_run_id=new_id("rptrun"),
            report_type=report_type,
            space_id=space_id,
            period_start=period_start,
            period_end=period_end,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO report_runs
                   (report_run_id, report_type, report_version, space_id,
                    period_start, period_end, input_snapshot_hash,
                    output_artifact_hash, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run.report_run_id, run.report_type, "", run.space_id,
                 run.period_start, run.period_end, "", "", run.status, run.created_at),
            )
        return run

    def complete_report(self, report_run_id: str, output_hash: str) -> None:
        with self.db.tx() as con:
            con.execute(
                "UPDATE report_runs SET status = ?, output_artifact_hash = ? WHERE report_run_id = ?",
                ("completed", output_hash, report_run_id),
            )

    def list_runs(self, report_type: str | None = None, space_id: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            query = "SELECT * FROM report_runs WHERE 1=1"
            params: list[Any] = []
            if report_type:
                query += " AND report_type = ?"
                params.append(report_type)
            if space_id:
                query += " AND space_id = ?"
                params.append(space_id)
            query += " ORDER BY created_at DESC"
            rows = con.execute(query, params).fetchall()
            return [dict(r) for r in rows]


class ShareRegistry:
    def __init__(self, db: Database):
        self.db = db

    def create_share(self, source_space_id: str, audience_type: str,
                     selection_spec: dict[str, Any] | None = None,
                     expires_at: str = "") -> SharePackage:
        share = SharePackage(
            share_id=new_id("share"),
            source_space_id=source_space_id,
            audience_type=audience_type,
            selection_spec=selection_spec or {},
            expires_at=expires_at,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO share_packages
                   (share_id, source_space_id, audience_type, policy_snapshot_hash,
                    selection_spec_json, artifact_hash, expires_at, revoked_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (share.share_id, share.source_space_id, share.audience_type,
                 share.policy_snapshot_hash, json.dumps(share.selection_spec),
                 share.artifact_hash, share.expires_at, share.revoked_at, share.created_at),
            )
        return share

    def revoke_share(self, share_id: str) -> None:
        with self.db.tx() as con:
            con.execute("UPDATE share_packages SET revoked_at = ? WHERE share_id = ?", (utc_now(), share_id))

    def list_shares(self, source_space_id: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if source_space_id:
                rows = con.execute(
                    "SELECT * FROM share_packages WHERE source_space_id = ? ORDER BY created_at DESC",
                    (source_space_id,),
                ).fetchall()
            else:
                rows = con.execute("SELECT * FROM share_packages ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
