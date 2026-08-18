from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from sandbox.lifegit.db import LifeDB
from sandbox.lifegit.pastme import snapshot


def query(db: LifeDB, endpoint: str, params: dict[str, list[str]]) -> tuple[int, object]:
    if endpoint == "/health":
        return 200, {"ok": True, "service": "lifegit"}
    if endpoint == "/stats":
        return 200, db.stats()
    if endpoint == "/objects":
        typ = (params.get("type") or [None])[0]
        limit = min(1000, int((params.get("limit") or [200])[0]))
        with db.connect() as con:
            sql = "SELECT object_id,object_type,canonical_text,first_observed_at,confidence,privacy_class,work_relevance,evidence_message_id FROM semantic_objects"
            args = []
            if typ:
                sql += " WHERE object_type=?"; args.append(typ.upper())
            sql += " ORDER BY first_observed_at DESC LIMIT ?"; args.append(limit)
            return 200, [dict(r) for r in con.execute(sql, args)]
    if endpoint == "/tensions":
        with db.connect() as con:
            return 200, [dict(r) for r in con.execute("SELECT * FROM tensions ORDER BY evidence_count DESC,last_observed_at DESC LIMIT 500")]
    if endpoint == "/career":
        with db.connect() as con:
            return 200, [dict(r) for r in con.execute("""SELECT object_id,object_type,canonical_text,first_observed_at,confidence,work_relevance,evidence_message_id
                FROM semantic_objects WHERE privacy_class='WORK_CANDIDATE' AND work_relevance>=0.45 ORDER BY first_observed_at DESC LIMIT 500""")]
    if endpoint == "/past":
        at = (params.get("at") or [None])[0]
        if not at:
            return 400, {"error": "missing ?at=YYYY-MM-DD"}
        return 200, snapshot(db, at)
    return 404, {"error": "not found"}


def serve(db_path: str, host: str = "127.0.0.1", port: int = 8787) -> None:
    db = LifeDB(db_path)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            try:
                status, body = query(db, u.path, parse_qs(u.query))
            except Exception as exc:
                status, body = 500, {"error": type(exc).__name__, "detail": str(exc)}
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, fmt, *args):
            return
    print(f"LifeGit read-only API: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
