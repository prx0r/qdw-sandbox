from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, *parts: object) -> str:
    body = canonical_json(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(body).hexdigest()[:24]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iso_time(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s).astimezone(timezone.utc).isoformat()
    except ValueError:
        return str(value)


def flatten_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out=[]
        for item in content:
            text=flatten_text(item)
            if text:
                out.append(text)
        return "\n".join(out)
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        if "parts" in content:
            return flatten_text(content["parts"])
        if "content" in content:
            return flatten_text(content["content"])
        # Do not stringify arbitrary tool payloads into personal narrative.
        return ""
    return str(content)


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def tokens(text: str) -> set[str]:
    stop={"the","and","that","this","with","from","have","what","when","where","would","could","should","about","into","your","you","for","are","was","were","how","why","can","its","it's","but","not","just","like","really","then","than","too","also","there","they","them","our","out"}
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t)>2 and t not in stop}


def jaccard(a: str, b: str) -> float:
    aa,bb=tokens(a),tokens(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb)/len(aa | bb)


def read_json_or_zip(path: Path, preferred_names: tuple[str, ...]) -> tuple[Any, bytes, str]:
    import zipfile
    raw=path.read_bytes()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            chosen=None
            for pref in preferred_names:
                exact=[n for n in names if n.lower().endswith(pref.lower())]
                if exact:
                    chosen=sorted(exact, key=len)[0]
                    break
            if chosen is None:
                raise ValueError(f"No expected JSON file in ZIP. looked for {preferred_names}")
            data=z.read(chosen)
            return json.loads(data.decode("utf-8")), raw, chosen
    return json.loads(raw.decode("utf-8")), raw, path.name
