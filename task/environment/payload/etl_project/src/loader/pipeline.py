from __future__ import annotations

import csv
from pathlib import Path

import yaml


CANONICAL_HEADER = ["shipment_id", "vendor_id", "business_date", "status", "amount_usd"]
HEADER_ALIASES = {
    "shipment_id": {"shipment_id", "shipmentid", "shipment", "shipment_ref", "shipment_no", "move_id"},
    "status": {"status", "status_text", "state"},
    "amount": {"amount"},
    "date": {"date", "business_date"},
}


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def load_profiles(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def infer_vendor_id(path: Path) -> str:
    stem = path.stem
    return stem.split("__", 1)[0]


def looks_numeric(value: str) -> bool:
    candidate = value.strip().replace(".", "", 1)
    return candidate.isdigit()


def parse_amount(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def parse_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return value.strip()


def find_columns(headers: list[str]) -> dict[str, int]:
    normalized = [normalize_header(item) for item in headers]
    columns = {
        "shipment_id": 0,
        "status": 1 if len(headers) > 1 else 0,
        "business_date": 2 if len(headers) > 2 else 0,
        "amount": 3 if len(headers) > 3 else max(0, len(headers) - 1),
    }
    for field, aliases in HEADER_ALIASES.items():
        for idx, name in enumerate(normalized):
            if name in aliases:
                columns[field] = idx
                break
    return columns


def first_date_like(cells: list[str]) -> str:
    for value in cells:
        parsed = parse_date(value)
        if parsed != value.strip() or "-" in value or "/" in value:
            return parsed
    return cells[0].strip() if cells else ""


def normalize_status(value: str) -> str:
    return value.strip().lower()


def row_is_empty(cells: list[str]) -> bool:
    return not any(item.strip() for item in cells)


def iter_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header: list[str] | None = None
        expected_width: int | None = None
        rows: list[dict[str, str]] = []
        columns: dict[str, int] | None = None
        for raw_row in reader:
            if row_is_empty(raw_row):
                continue
            if header is None:
                header = raw_row
                columns = find_columns(header)
                continue
            if expected_width is None:
                expected_width = len(raw_row)
            if len(raw_row) != expected_width:
                continue
            assert columns is not None
            amount_index = columns["amount"]
            if normalize_header(header[amount_index]) != "amount":
                for idx, value in enumerate(raw_row):
                    if looks_numeric(value):
                        amount_index = idx
                        break
            row = {
                "shipment_id": raw_row[columns["shipment_id"]].strip(),
                "business_date": first_date_like(raw_row),
                "status": normalize_status(raw_row[columns["status"]]),
                "amount_usd": f"{parse_amount(raw_row[amount_index]):.2f}",
            }
            rows.append(row)
        return rows


def run_load(input_dir: Path, profiles_path: Path, out_dir: Path) -> Path:
    load_profiles(profiles_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / "shipments_normalized.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CANONICAL_HEADER)
        for csv_path in sorted(input_dir.glob("*.csv")):
            vendor_id = infer_vendor_id(csv_path)
            for row in iter_rows(csv_path):
                writer.writerow(
                    [
                        row["shipment_id"],
                        vendor_id,
                        row["business_date"],
                        row["status"],
                        row["amount_usd"],
                    ]
                )
    return destination
