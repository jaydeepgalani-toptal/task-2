from __future__ import annotations

import json
from pathlib import Path

from oracle_loader import build_expected_json, sha256


ROOT = Path("/workspace/etl")
INPUT_DIR = ROOT / "data" / "vendor_exports"
PROFILE_PATH = ROOT / "data" / "vendor_profiles.yaml"
MANIFEST_PATH = Path("/opt/etl_support/protected_hashes.json")
EXPECTED_PATH = Path("/opt/etl_support/expected_aggregates.json")


def main() -> None:
    build_expected_json(INPUT_DIR, PROFILE_PATH, EXPECTED_PATH)
    records: dict[str, str] = {
        str(ROOT / "bin" / "run-load"): sha256(ROOT / "bin" / "run-load"),
        str(ROOT / "pyproject.toml"): sha256(ROOT / "pyproject.toml"),
        str(ROOT / "uv.lock"): sha256(ROOT / "uv.lock"),
        str(PROFILE_PATH): sha256(PROFILE_PATH),
    }
    for csv_path in sorted(INPUT_DIR.glob("*.csv")):
        records[str(csv_path)] = sha256(csv_path)
    MANIFEST_PATH.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
