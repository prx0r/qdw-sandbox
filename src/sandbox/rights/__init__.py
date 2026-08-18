"""Rights module — data grants and access control."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import DataGrant, new_id, utc_now


class GrantRegistry:
    def __init__(self, db: Database):
        self.db = db

    def create_grant(self, owner_entity_id: str, source_space_id: str,
                     grantee_entity_id: str, purpose_term_id: str,
                     scope: dict[str, Any] | None = None,
                     allowed_operations: tuple[str, ...] = (),
                     raw_access: bool = False, training_allowed: bool = False,
                     redistribution_allowed: bool = False,
                     valid_from: str = "", valid_until: str = "",
                     rights_backend: str = "native_local") -> DataGrant:
        grant = DataGrant(
            grant_id=new_id("grant"),
            owner_entity_id=owner_entity_id,
            source_space_id=source_space_id,
            grantee_entity_id=grantee_entity_id,
            purpose_term_id=purpose_term_id,
            scope=scope or {},
            allowed_operations=allowed_operations,
            raw_access=raw_access,
            training_allowed=training_allowed,
            redistribution_allowed=redistribution_allowed,
            valid_from=valid_from or utc_now(),
            valid_until=valid_until,
            rights_backend=rights_backend,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO data_grants
                   (grant_id, owner_entity_id, source_space_id, grantee_entity_id,
                    purpose_term_id, scope_json, allowed_operations_json,
                    raw_access, training_allowed, redistribution_allowed,
                    valid_from, valid_until, revoked_at, rights_backend, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (grant.grant_id, grant.owner_entity_id, grant.source_space_id,
                 grant.grantee_entity_id, grant.purpose_term_id, json.dumps(grant.scope),
                 json.dumps(list(grant.allowed_operations)),
                 1 if grant.raw_access else 0, 1 if grant.training_allowed else 0,
                 1 if grant.redistribution_allowed else 0,
                 grant.valid_from, grant.valid_until, grant.revoked_at,
                 grant.rights_backend, grant.created_at),
            )
        return grant

    def revoke_grant(self, grant_id: str) -> None:
        with self.db.tx() as con:
            con.execute("UPDATE data_grants SET revoked_at = ? WHERE grant_id = ?", (utc_now(), grant_id))

    def check_grant(self, source_space_id: str, grantee_entity_id: str, purpose_term_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                """SELECT * FROM data_grants
                   WHERE source_space_id = ? AND grantee_entity_id = ? AND purpose_term_id = ?
                   AND (valid_until = '' OR valid_until > ?)
                   AND (revoked_at = '' OR revoked_at > ?)""",
                (source_space_id, grantee_entity_id, purpose_term_id, utc_now(), utc_now()),
            ).fetchone()
            return dict(row) if row else None

    def list_grants(self, owner_entity_id: str | None = None, source_space_id: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            query = "SELECT * FROM data_grants WHERE 1=1"
            params: list[Any] = []
            if owner_entity_id:
                query += " AND owner_entity_id = ?"
                params.append(owner_entity_id)
            if source_space_id:
                query += " AND source_space_id = ?"
                params.append(source_space_id)
            query += " ORDER BY created_at DESC"
            rows = con.execute(query, params).fetchall()
            return [dict(r) for r in rows]
