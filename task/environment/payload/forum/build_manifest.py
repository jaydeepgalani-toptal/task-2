from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROTECTED_PATHS = [
    "/workspace/bin/download-mods",
    "/workspace/pyproject.toml",
    "/workspace/uv.lock",
    "/usr/local/bin/forum-serverctl",
    "/etc/profile.d/forum_env.sh",
    "/opt/localforum/run_server.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    records: dict[str, str] = {}
    for raw in PROTECTED_PATHS:
        path = Path(raw)
        records[str(path)] = sha256(path)
    for path in sorted(Path("/opt/localforum/fixtures").rglob("*")):
        if path.is_dir():
            continue
        if path.suffix not in {".json", ".zip"}:
            continue
        records[str(path)] = sha256(path)
    output = Path("/opt/localforum/protected_hashes.json")
    output.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
