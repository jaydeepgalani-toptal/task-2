from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from dateutil import parser as date_parser
import yaml


CANONICAL_HEADER = ["shipment_id", "vendor_id", "business_date", "status", "amount_usd"]
VALID_STATUSES = {"shipped", "delivered", "cancelled", "returned", "in_transit"}
SHIPMENT_FIELDS = {
    "shipment_id",
    "shipment_ref",
    "load_ref",
    "consignment_id",
    "shipment_consignment",
    "move_id",
    "move_identifier",
    "shipment_no",
    "shipment_number",
    "dispatch_id",
    "dispatch_reference",
    "freight_id",
    "freight_reference",
}
STATUS_FIELDS = {"status", "current_state", "state_label", "progress", "ledger_status", "status_text", "movement_state", "status_name"}
ALIAS_MAP = {
    "shipmentid": "shipment_id",
    "shipment_ref": "shipment_ref",
    "load_ref": "shipment_ref",
    "current_state": "current_state",
    "state_label": "current_state",
    "settlement_dt": "settlement_date",
    "settled_on": "settlement_date",
    "gross_charge_usd": "gross_charge",
    "amount_due": "amount",
    "shipment_consignment": "consignment_id",
    "remit_dt": "remit_date",
    "net_amount_usd": "net_amount",
    "move_identifier": "move_id",
    "invoice_total_usd": "invoice_total",
    "ledger_dt": "ledger_date",
    "shipment_number": "shipment_no",
    "acct_date": "accounting_date",
    "bill_amount_usd": "bill_amount",
    "dispatch_reference": "dispatch_id",
    "settlement_amount_usd": "settlement_amount",
    "close_dt": "close_date",
    "freight_reference": "freight_id",
    "revenue_amount_usd": "revenue_amount",
    "recognized_dt": "recognized_date",
    "remitdate": "remit_date",
}


def normalize_header(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return ALIAS_MAP.get(text, text)


def parse_amount(value: str) -> Decimal:
    raw = value.strip()
    if not raw:
        raise ValueError("missing amount")
    negative = raw.startswith("(") and raw.endswith(")")
    cleaned = raw.strip("()").replace("$", "").replace(",", "").replace("USD", "").strip()
    amount = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return -amount if negative else amount


def parse_business_date(value: str) -> str:
    raw = value.strip()
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", raw):
        parsed = date_parser.parse(raw, dayfirst=True).date()
    else:
        parsed = date_parser.parse(raw).date()
    return parsed.isoformat()


def is_noise_row(row: list[str]) -> bool:
    if not row:
        return True
    stripped = [cell.strip() for cell in row]
    if not any(stripped):
        return True
    first = stripped[0]
    if first.startswith("#"):
        return True
    if first.upper() in {"TOTAL", "SUMMARY"}:
        return True
    if "end of report" in first.lower():
        return True
    return False


@dataclass(frozen=True)
class Record:
    shipment_id: str
    vendor_id: str
    business_date: str
    status: str
    amount_usd: str


def load_profiles(path: Path) -> dict[str, dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def header_index_map(headers: list[str]) -> dict[str, int]:
    return {normalize_header(name): idx for idx, name in enumerate(headers)}


def status_field_name(header_map: dict[str, int]) -> str:
    for field in STATUS_FIELDS:
        if field in header_map:
            return field
    raise KeyError("status field not found")


def shipment_field_name(header_map: dict[str, int]) -> str:
    for field in SHIPMENT_FIELDS:
        if field in header_map:
            return field
    raise KeyError("shipment field not found")


def amount_field_name(header_map: dict[str, int], profile: dict) -> str:
    preferred = normalize_header(profile["amount_field"])
    if preferred in header_map:
        return preferred
    if "amount" in header_map:
        return "amount"
    for key in header_map:
        if "amount" in key or key.endswith("_charge") or key.endswith("_total"):
            return key
    raise KeyError("amount field not found")


def business_field_name(header_map: dict[str, int], profile: dict) -> str:
    preferred = normalize_header(profile["business_date_field"])
    if preferred in header_map:
        return preferred
    raise KeyError("business date field not found")


def canonical_records(input_dir: Path, profiles_path: Path) -> list[Record]:
    profiles = load_profiles(profiles_path)
    records: list[Record] = []
    for csv_path in sorted(input_dir.glob("*.csv")):
        vendor_id = csv_path.stem.split("__", 1)[0]
        profile = profiles[vendor_id]
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader)
            header_map = header_index_map(headers)
            shipment_key = shipment_field_name(header_map)
            status_key = status_field_name(header_map)
            amount_key = amount_field_name(header_map, profile)
            business_key = business_field_name(header_map, profile)
            for row in reader:
                if is_noise_row(row):
                    continue
                if len(row) < len(headers):
                    row = row + [""] * (len(headers) - len(row))
                if len(row) > len(headers):
                    row = row[: len(headers)]
                shipment_id = row[header_map[shipment_key]].strip()
                status_raw = row[header_map[status_key]].strip()
                amount_raw = row[header_map[amount_key]].strip()
                business_raw = row[header_map[business_key]].strip()
                if not shipment_id:
                    continue
                status = profile["status_map"][status_raw]
                amount = parse_amount(amount_raw)
                business_date = parse_business_date(business_raw)
                records.append(
                    Record(
                        shipment_id=shipment_id,
                        vendor_id=vendor_id,
                        business_date=business_date,
                        status=status,
                        amount_usd=f"{amount:.2f}",
                    )
                )
    return records


def write_output(records: list[Record], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / "shipments_normalized.csv"
    ordered = sorted(records, key=lambda item: (item.vendor_id, item.shipment_id))
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CANONICAL_HEADER)
        for record in ordered:
            writer.writerow([record.shipment_id, record.vendor_id, record.business_date, record.status, record.amount_usd])
    return destination


def monthly_aggregates(records: list[Record]) -> dict[str, dict[str, dict[str, str]]]:
    grouped: dict[str, dict[str, dict[str, Decimal | int]]] = defaultdict(lambda: defaultdict(lambda: {"rows": 0, "amount": Decimal("0.00")}))
    for record in records:
        month_key = record.business_date[:7]
        bucket = grouped[record.vendor_id][month_key]
        bucket["rows"] += 1
        bucket["amount"] += Decimal(record.amount_usd)
    output: dict[str, dict[str, dict[str, str]]] = {}
    for vendor_id, months in grouped.items():
        output[vendor_id] = {}
        for month_key, values in months.items():
            output[vendor_id][month_key] = {
                "rows": int(values["rows"]),
                "amount": f"{values['amount'].quantize(Decimal('0.01')):.2f}",
            }
    return output


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def build_expected_json(input_dir: Path, profiles_path: Path, destination: Path) -> None:
    records = canonical_records(input_dir, profiles_path)
    payload = {
        "header": CANONICAL_HEADER,
        "row_count": len(records),
        "aggregates": monthly_aggregates(records),
        "negative_cancelled": sum(1 for record in records if Decimal(record.amount_usd) < 0 and record.status == "cancelled"),
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
