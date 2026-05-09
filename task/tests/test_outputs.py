from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest


ROOT = Path("/workspace/etl")
OUT_DIR = ROOT / "out"
OUTPUT_PATH = OUT_DIR / "shipments_normalized.csv"
INPUT_DIR = ROOT / "data" / "vendor_exports"
PROFILE_PATH = ROOT / "data" / "vendor_profiles.yaml"
EXPECTED_PATH = Path("/opt/etl_support/expected_aggregates.json")
MANIFEST_PATH = Path("/opt/etl_support/protected_hashes.json")
VALID_STATUSES = {"shipped", "delivered", "cancelled", "returned", "in_transit"}
VENDOR_IDS = {
    "atlas_freight",
    "bluewave_logistics",
    "copperpoint_carriers",
    "delta_brokerage",
    "evergreen_dispatch",
    "foxglove_freight",
}


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def run_loader() -> list[dict[str, str]]:
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    env = os.environ.copy()
    subprocess.run(
        ["./bin/run-load", "--in", "data/vendor_exports/", "--profiles", "data/vendor_profiles.yaml", "--out", "out/"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    assert OUTPUT_PATH.exists(), "expected normalized CSV was not created"
    with OUTPUT_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sorted_rows(rows: list[dict[str, str]]) -> list[tuple[str, str, str, str, str]]:
    return sorted(
        (
            row["shipment_id"],
            row["vendor_id"],
            row["business_date"],
            row["status"],
            row["amount_usd"],
        )
        for row in rows
    )


def aggregates(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    grouped: dict[str, dict[str, dict[str, Decimal | int]]] = {}
    for row in rows:
        vendor_id = row["vendor_id"]
        month_key = row["business_date"][:7]
        vendor_bucket = grouped.setdefault(vendor_id, {})
        month_bucket = vendor_bucket.setdefault(month_key, {"rows": 0, "amount": Decimal("0.00")})
        month_bucket["rows"] += 1
        month_bucket["amount"] += Decimal(row["amount_usd"])
    result: dict[str, dict[str, dict[str, str]]] = {}
    for vendor_id, months in grouped.items():
        result[vendor_id] = {}
        for month_key, values in months.items():
            result[vendor_id][month_key] = {
                "rows": int(values["rows"]),
                "amount": f"{values['amount'].quantize(Decimal('0.01')):.2f}",
            }
    return result


@pytest.fixture(scope="session")
def expected() -> dict:
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def run_results() -> dict[str, object]:
    first_rows = run_loader()
    second_rows = run_loader()
    return {"first": first_rows, "second": second_rows}


def test_output_exists_and_is_non_empty(run_results: dict[str, object]) -> None:
    rows = run_results["first"]
    assert OUTPUT_PATH.exists()
    assert OUTPUT_PATH.stat().st_size > 0
    assert rows


def test_header_is_exact(expected: dict) -> None:
    with OUTPUT_PATH.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    assert header == expected["header"]


def test_row_count_is_exact(run_results: dict[str, object], expected: dict) -> None:
    assert len(run_results["first"]) == expected["row_count"] == 3000


def test_every_business_date_is_iso(run_results: dict[str, object]) -> None:
    for row in run_results["first"]:
        assert row["business_date"] == date.fromisoformat(row["business_date"]).isoformat()


def test_every_status_is_canonical(run_results: dict[str, object]) -> None:
    assert {row["status"] for row in run_results["first"]}.issubset(VALID_STATUSES)


def test_every_vendor_is_expected(run_results: dict[str, object]) -> None:
    assert {row["vendor_id"] for row in run_results["first"]} == VENDOR_IDS


def test_monthly_counts_and_totals_match_oracle(run_results: dict[str, object], expected: dict) -> None:
    actual = aggregates(run_results["first"])
    for vendor_id, months in expected["aggregates"].items():
        assert vendor_id in actual
        for month_key, values in months.items():
            assert actual[vendor_id][month_key]["rows"] == values["rows"]
            assert abs(Decimal(actual[vendor_id][month_key]["amount"]) - Decimal(values["amount"])) <= Decimal("0.01")


def test_negative_cancelled_rows_count(run_results: dict[str, object], expected: dict) -> None:
    negative_cancelled = [
        row
        for row in run_results["first"]
        if Decimal(row["amount_usd"]) < 0 and row["status"] == "cancelled"
    ]
    assert len(negative_cancelled) == expected["negative_cancelled"] == 12


def test_second_run_is_identical_after_sorting(run_results: dict[str, object]) -> None:
    assert sorted_rows(run_results["first"]) == sorted_rows(run_results["second"])


def test_protected_inputs_and_entrypoint_are_unchanged() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for raw_path, expected_hash in manifest.items():
        path = Path(raw_path)
        assert path.exists(), f"protected path missing: {path}"
        assert sha256(path) == expected_hash, f"protected path changed: {path}"
