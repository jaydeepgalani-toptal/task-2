from __future__ import annotations

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import yaml

from oracle_loader import canonical_records, header_index_map, is_noise_row, load_profiles, normalize_header, parse_business_date


ROOT = Path("/workspace/etl")
INPUT_DIR = ROOT / "data" / "vendor_exports"
PROFILE_PATH = ROOT / "data" / "vendor_profiles.yaml"


def looks_supported_date(raw: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw) or re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw))


def looks_dmy(raw: str) -> bool:
    return bool(re.fullmatch(r"\d{2}-\d{2}-\d{4}", raw))


def looks_dateish(raw: str) -> bool:
    value = raw.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T.*)?", value):
        return True
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return True
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", value):
        return True
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}", value):
        return True
    if re.fullmatch(r"[A-Z][a-z]{2} \d{1,2} \d{4}", value):
        return True
    return False


def monthly_aggregates(records) -> dict[str, dict[str, tuple[int, Decimal]]]:
    grouped: dict[str, dict[str, tuple[int, Decimal]]] = defaultdict(lambda: defaultdict(lambda: (0, Decimal("0.00"))))
    for record in records:
        month_key = record.business_date[:7]
        rows, amount = grouped[record.vendor_id][month_key]
        grouped[record.vendor_id][month_key] = (rows + 1, amount + Decimal(record.amount_usd))
    return grouped


def alternate_monthly_aggregates() -> dict[str, dict[str, tuple[int, Decimal]]]:
    profiles = load_profiles(PROFILE_PATH)
    grouped: dict[str, dict[str, tuple[int, Decimal]]] = defaultdict(lambda: defaultdict(lambda: (0, Decimal("0.00"))))
    for csv_path in sorted(INPUT_DIR.glob("*.csv")):
        vendor_id = csv_path.stem.split("__", 1)[0]
        profile = profiles[vendor_id]
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader)
            header_map = header_index_map(headers)
            amount_key = normalize_header(profile["amount_field"])
            if amount_key not in header_map and "amount" in header_map:
                amount_key = "amount"
            for row in reader:
                if is_noise_row(row):
                    continue
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                first_date = None
                for value in row:
                    if looks_dateish(value):
                        first_date = parse_business_date(value)
                        break
                if not first_date:
                    continue
                amount_raw = row[header_map[amount_key]].strip()
                cleaned = amount_raw.strip("()").replace("$", "").replace(",", "").replace("USD", "").strip()
                amount = Decimal(cleaned)
                if amount_raw.strip().startswith("(") and amount_raw.strip().endswith(")"):
                    amount = -amount
                month_key = first_date[:7]
                rows, total = grouped[vendor_id][month_key]
                grouped[vendor_id][month_key] = (rows + 1, total + amount)
    return grouped


def main() -> None:
    records = canonical_records(INPUT_DIR, PROFILE_PATH)
    assert len(list(INPUT_DIR.glob("*.csv"))) == 60
    assert len(records) == 3000
    assert sum(1 for record in records if Decimal(record.amount_usd) < 0 and record.status == "cancelled") == 12

    profiles = load_profiles(PROFILE_PATH)
    non_iso_business_dates = 0
    dmy_rows = 0
    dmy_high_day_rows = 0
    for csv_path in sorted(INPUT_DIR.glob("*.csv")):
        vendor_id = csv_path.stem.split("__", 1)[0]
        profile = profiles[vendor_id]
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader)
            header_map = header_index_map(headers)
            business_key = normalize_header(profile["business_date_field"])
            for row in reader:
                if is_noise_row(row):
                    continue
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                raw_business = row[header_map[business_key]].strip()
                if not looks_supported_date(raw_business):
                    non_iso_business_dates += 1
                if looks_dmy(raw_business):
                    dmy_rows += 1
                    if int(raw_business[:2]) > 12:
                        dmy_high_day_rows += 1

    assert 500 <= non_iso_business_dates <= 700
    assert dmy_rows > 0
    assert dmy_high_day_rows * 2 >= dmy_rows

    correct = monthly_aggregates(records)
    alternate = alternate_monthly_aggregates()
    differing_vendors = 0
    for vendor_id, months in correct.items():
        if months != alternate[vendor_id]:
            differing_vendors += 1
    assert differing_vendors >= 4


if __name__ == "__main__":
    main()
