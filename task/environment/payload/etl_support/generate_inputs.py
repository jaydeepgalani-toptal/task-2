from __future__ import annotations

import csv
import random
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import yaml


random.seed(42)

ROOT = Path("/workspace/etl")
DATA_DIR = ROOT / "data"
EXPORT_DIR = DATA_DIR / "vendor_exports"
PROFILE_PATH = DATA_DIR / "vendor_profiles.yaml"

VENDORS = [
    {
        "vendor_id": "atlas_freight",
        "shipment_prefix": "ATL",
        "shipment_field": "shipment_ref",
        "status_field": "current_state",
        "business_date_field": "settlement_date",
        "amount_field": "gross_charge",
        "other_dates": ["pickup_date", "posted_ts"],
        "incidental": ["lane_code", "dispatcher_note"],
        "header_variants": [
            ["shipment_ref", "pickup_date", "settlement_date", "current_state", "gross_charge", "posted_ts", "lane_code", "dispatcher_note"],
            ["current_state", "shipment_ref", "pickup_date", "gross_charge", "settlement_dt", "posted_ts", "lane_code", "dispatcher_note"],
            ["posted_ts", "shipment_ref", "state_label", "pickup_date", "gross_charge_usd", "settlement_date", "lane_code", "dispatcher_note"],
            ["pickup_date", "shipment_ref", "gross_charge", "current_state", "settled_on", "posted_ts", "lane_code", "dispatcher_note", "portal_batch"],
        ],
        "status_variants": {
            "shipped": ["Manifested", "Released", "SHIPPED"],
            "delivered": ["Delivered", "Proofed", "DELIVERED"],
            "cancelled": ["Canceled", "Voided", "Cancelled"],
            "returned": ["Returned", "RTS", "Return Complete"],
            "in_transit": ["In Transit", "Linehaul", "IN TRANSIT"],
        },
        "supported_date_format": "iso",
        "unsupported_date_format": "text",
        "amount_formats": ["plain", "currency"],
    },
    {
        "vendor_id": "bluewave_logistics",
        "shipment_prefix": "BLU",
        "shipment_field": "consignment_id",
        "status_field": "progress",
        "business_date_field": "remit_date",
        "amount_field": "net_amount",
        "other_dates": ["created_on", "depart_date"],
        "incidental": ["region_name", "broker_note"],
        "header_variants": [
            ["consignment_id", "created_on", "depart_date", "progress", "net_amount", "remit_date", "region_name", "broker_note"],
            ["progress", "consignment_id", "depart_date", "amount_due", "created_on", "remit_date", "region_name", "broker_note"],
            ["created_on", "shipment_consignment", "progress", "depart_date", "net_amount", "remit_dt", "region_name", "broker_note", "loaded_by"],
            ["depart_date", "consignment_id", "progress", "created_on", "remit_date", "net_amount_usd", "region_name", "broker_note"],
        ],
        "status_variants": {
            "shipped": ["Booked", "Dispatched", "SHIPPED"],
            "delivered": ["Delivered", "Closed", "DELIVERED"],
            "cancelled": ["Canceled", "Cancelled", "Void"],
            "returned": ["Returned", "Backhaul Return", "RETURNED"],
            "in_transit": ["In Transit", "On Route", "IN TRANSIT"],
        },
        "supported_date_format": "mdy",
        "unsupported_date_format": "slash",
        "amount_formats": ["comma", "usd"],
    },
    {
        "vendor_id": "copperpoint_carriers",
        "shipment_prefix": "COP",
        "shipment_field": "move_id",
        "status_field": "ledger_status",
        "business_date_field": "ledger_date",
        "amount_field": "invoice_total",
        "other_dates": ["scan_time", "ship_date"],
        "incidental": ["yard_slot", "service_level"],
        "header_variants": [
            ["move_id", "scan_time", "ship_date", "ledger_status", "invoice_total", "ledger_date", "yard_slot", "service_level"],
            ["ledger_status", "move_id", "ship_date", "invoice_total", "scan_time", "ledger_date", "yard_slot", "service_level"],
            ["scan_time", "move_identifier", "ledger_status", "ship_date", "invoice_total_usd", "ledger_dt", "yard_slot", "service_level", "source_file"],
            ["ship_date", "move_id", "ledger_status", "scan_time", "ledger_date", "invoice_total", "yard_slot", "service_level"],
        ],
        "status_variants": {
            "shipped": ["Tendered", "Released", "SHIPPED"],
            "delivered": ["Delivered", "Pod Logged", "DELIVERED"],
            "cancelled": ["Cancelled", "Canceled", "Adjustment Cancel"],
            "returned": ["Returned", "Returned To Sender", "RETURNED"],
            "in_transit": ["In Transit", "En Route", "IN TRANSIT"],
        },
        "supported_date_format": "iso",
        "unsupported_date_format": "dmy",
        "amount_formats": ["paren", "plain"],
    },
    {
        "vendor_id": "delta_brokerage",
        "shipment_prefix": "DEL",
        "shipment_field": "shipment_no",
        "status_field": "status_text",
        "business_date_field": "accounting_date",
        "amount_field": "bill_amount",
        "other_dates": ["created_at", "drop_date"],
        "incidental": ["account_rep", "mode_name"],
        "header_variants": [
            ["shipment_no", "created_at", "drop_date", "status_text", "bill_amount", "accounting_date", "account_rep", "mode_name"],
            ["status_text", "shipment_no", "drop_date", "created_at", "amount_due", "accounting_date", "account_rep", "mode_name"],
            ["created_at", "shipment_number", "status_text", "drop_date", "bill_amount", "acct_date", "account_rep", "mode_name", "exported_by"],
            ["drop_date", "shipment_no", "status_text", "created_at", "accounting_date", "bill_amount_usd", "account_rep", "mode_name"],
        ],
        "status_variants": {
            "shipped": ["Booked", "Tendered", "SHIPPED"],
            "delivered": ["Delivered", "Settled", "DELIVERED"],
            "cancelled": ["Canceled", "Cancelled", "Broker Cancelled"],
            "returned": ["Returned", "Recovery Return", "RETURNED"],
            "in_transit": ["In Transit", "Moving", "IN TRANSIT"],
        },
        "supported_date_format": "mdy",
        "unsupported_date_format": "text",
        "amount_formats": ["currency", "comma"],
    },
    {
        "vendor_id": "evergreen_dispatch",
        "shipment_prefix": "EVE",
        "shipment_field": "dispatch_id",
        "status_field": "movement_state",
        "business_date_field": "close_date",
        "amount_field": "settlement_amount",
        "other_dates": ["order_date", "export_ts"],
        "incidental": ["planner", "lane_family"],
        "header_variants": [
            ["dispatch_id", "order_date", "export_ts", "movement_state", "settlement_amount", "close_date", "planner", "lane_family"],
            ["movement_state", "dispatch_id", "order_date", "amount_due", "close_date", "export_ts", "planner", "lane_family"],
            ["export_ts", "dispatch_reference", "movement_state", "order_date", "settlement_amount_usd", "close_dt", "planner", "lane_family", "extract_batch"],
            ["order_date", "dispatch_id", "movement_state", "export_ts", "settlement_amount", "close_date", "planner", "lane_family"],
        ],
        "status_variants": {
            "shipped": ["Assigned", "Tendered", "SHIPPED"],
            "delivered": ["Delivered", "Closed", "DELIVERED"],
            "cancelled": ["Cancelled", "Canceled", "Dispatch Void"],
            "returned": ["Returned", "Return", "RETURNED"],
            "in_transit": ["In Transit", "Running", "IN TRANSIT"],
        },
        "supported_date_format": "iso",
        "unsupported_date_format": "dmy",
        "amount_formats": ["usd", "plain"],
    },
    {
        "vendor_id": "foxglove_freight",
        "shipment_prefix": "FOX",
        "shipment_field": "freight_id",
        "status_field": "status_name",
        "business_date_field": "recognized_date",
        "amount_field": "revenue_amount",
        "other_dates": ["tendered_at", "completed_on"],
        "incidental": ["terminal", "ops_note"],
        "header_variants": [
            ["freight_id", "tendered_at", "completed_on", "status_name", "revenue_amount", "recognized_date", "terminal", "ops_note"],
            ["status_name", "freight_id", "completed_on", "revenue_amount", "tendered_at", "recognized_date", "terminal", "ops_note"],
            ["tendered_at", "freight_reference", "status_name", "completed_on", "revenue_amount_usd", "recognized_dt", "terminal", "ops_note", "portal_user"],
            ["completed_on", "freight_id", "status_name", "tendered_at", "recognized_date", "revenue_amount", "terminal", "ops_note"],
        ],
        "status_variants": {
            "shipped": ["Booked", "Tendered", "SHIPPED"],
            "delivered": ["Delivered", "Accepted", "DELIVERED"],
            "cancelled": ["Cancelled", "Canceled", "Finance Cancelled"],
            "returned": ["Returned", "Return Load", "RETURNED"],
            "in_transit": ["In Transit", "Hauling", "IN TRANSIT"],
        },
        "supported_date_format": "mdy",
        "unsupported_date_format": "iso_tz",
        "amount_formats": ["comma", "currency"],
    },
]

STATUS_PATTERN = [
    "shipped",
    "in_transit",
    "delivered",
    "delivered",
    "returned",
    "delivered",
    "shipped",
    "in_transit",
    "delivered",
    "delivered",
]

CORRECTION_FILES = {1, 7}


def format_business_date(value: date, fmt_name: str) -> str:
    if fmt_name == "iso":
        return value.isoformat()
    if fmt_name == "mdy":
        return value.strftime("%m/%d/%Y")
    if fmt_name == "dmy":
        return value.strftime("%d-%m-%Y")
    if fmt_name == "slash":
        return value.strftime("%Y/%m/%d")
    if fmt_name == "text":
        return value.strftime("%b") + f" {value.day} {value.year}"
    if fmt_name == "iso_dt":
        return f"{value.isoformat()}T14:30:00"
    if fmt_name == "iso_tz":
        return f"{value.isoformat()}T14:30:00+00:00"
    raise ValueError(fmt_name)


def format_other_date(value: date, style: str, use_offset_hours: bool = False) -> str:
    if style == "iso_tz":
        return f"{value.isoformat()}T08:15:00+00:00"
    if style == "iso_dt":
        return f"{value.isoformat()}T08:15:00"
    if style == "slash":
        return value.strftime("%Y/%m/%d")
    if style == "mdy":
        return value.strftime("%m/%d/%Y")
    if style == "dmy":
        return value.strftime("%d-%m-%Y")
    if style == "text":
        return value.strftime("%b") + f" {value.day} {value.year}"
    return value.isoformat()


def format_amount(value: Decimal, fmt_name: str) -> str:
    quantized = value.quantize(Decimal("0.01"))
    sign = "-" if quantized < 0 else ""
    absolute = abs(quantized)
    if fmt_name == "plain":
        return f"{quantized:.2f}"
    if fmt_name == "currency":
        return f"{sign}${absolute:.2f}"
    if fmt_name == "comma":
        return f"{quantized:,.2f}"
    if fmt_name == "paren":
        if quantized < 0:
            return f"({absolute:.2f})"
        return f"{absolute:.2f}"
    if fmt_name == "usd":
        return f"{quantized:.2f} USD"
    raise ValueError(fmt_name)


def vendor_profiles() -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for vendor in VENDORS:
        status_map = {}
        for canonical, variants in vendor["status_variants"].items():
            for variant in variants:
                status_map[variant] = canonical
        profiles[vendor["vendor_id"]] = {
            "business_date_field": vendor["business_date_field"],
            "amount_field": vendor["amount_field"],
            "status_map": status_map,
        }
    return profiles


def business_date_for(file_index: int, row_index: int) -> date:
    month = ((file_index - 1) // 2) + 1
    if row_index % 5 == 0:
        day = 2 + (row_index % 4)
    else:
        day = 13 + (row_index % 14)
    return date(2024, month, day)


def make_row(vendor: dict, file_index: int, row_index: int, sequence: int) -> dict[str, str]:
    business_date = business_date_for(file_index, row_index)
    ship_date = business_date - timedelta(days=5)
    if ship_date.month == business_date.month:
        ship_date = business_date - timedelta(days=8)
    other_date = business_date + timedelta(days=2)
    is_correction = row_index == 11 and file_index in CORRECTION_FILES
    canonical_status = "cancelled" if is_correction else STATUS_PATTERN[(file_index + row_index) % len(STATUS_PATTERN)]
    status_variant = vendor["status_variants"][canonical_status][(file_index + row_index) % 3]
    amount_value = Decimal("95.50") + Decimal(file_index * 11 + row_index) * Decimal("3.17")
    if row_index % 13 == 0:
        amount_value += Decimal("1000.25")
    if is_correction:
        amount_value = -(Decimal("40.00") + Decimal(file_index * 3))

    non_iso_rows = set(range(0, 10))
    date_format = vendor["unsupported_date_format"] if row_index in non_iso_rows else vendor["supported_date_format"]
    amount_format = vendor["amount_formats"][row_index % len(vendor["amount_formats"])]

    shipment_id = f"{vendor['shipment_prefix']}-{file_index:02d}-{sequence:04d}"
    row = {
        vendor["shipment_field"]: shipment_id,
        vendor["status_field"]: status_variant,
        vendor["business_date_field"]: format_business_date(business_date, date_format),
        vendor["amount_field"]: format_amount(amount_value, amount_format),
        vendor["other_dates"][0]: format_other_date(ship_date, "iso"),
        vendor["other_dates"][1]: format_other_date(other_date, vendor["unsupported_date_format"]),
        vendor["incidental"][0]: f"zone-{(file_index + row_index) % 7}",
        vendor["incidental"][1]: f"note-{sequence % 9}",
        "portal_batch": f"BATCH-{file_index:02d}",
        "loaded_by": f"user-{file_index % 4}",
        "source_file": f"source-{file_index:02d}",
        "exported_by": f"broker-{file_index % 5}",
        "extract_batch": f"EX-{file_index:02d}",
        "portal_user": f"portal-{file_index % 6}",
    }
    return row


def mapped_value(row: dict[str, str], header_name: str, vendor: dict) -> str:
    alias_map = {
        "settlement_dt": vendor["business_date_field"],
        "settled_on": vendor["business_date_field"],
        "state_label": vendor["status_field"],
        "gross_charge_usd": vendor["amount_field"],
        "amount_due": vendor["amount_field"],
        "shipment_consignment": vendor["shipment_field"],
        "remit_dt": vendor["business_date_field"],
        "net_amount_usd": vendor["amount_field"],
        "move_identifier": vendor["shipment_field"],
        "invoice_total_usd": vendor["amount_field"],
        "ledger_dt": vendor["business_date_field"],
        "shipment_number": vendor["shipment_field"],
        "acct_date": vendor["business_date_field"],
        "bill_amount_usd": vendor["amount_field"],
        "dispatch_reference": vendor["shipment_field"],
        "settlement_amount_usd": vendor["amount_field"],
        "close_dt": vendor["business_date_field"],
        "freight_reference": vendor["shipment_field"],
        "revenue_amount_usd": vendor["amount_field"],
        "recognized_dt": vendor["business_date_field"],
    }
    source_key = alias_map.get(header_name, header_name)
    return row.get(source_key, "")


def write_vendor_file(vendor: dict, file_index: int) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"{vendor['vendor_id']}__ledger_{file_index:02d}.csv"
    header = vendor["header_variants"][(file_index - 1) % len(vendor["header_variants"])]
    sequence_start = (file_index - 1) * 50
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow([f"# export generated for {vendor['vendor_id']}"] + [""] * (len(header) - 1))
        for row_index in range(50):
            row = make_row(vendor, file_index, row_index, sequence_start + row_index + 1)
            writer.writerow([mapped_value(row, column, vendor) for column in header])
            if row_index in {8, 31}:
                writer.writerow([])
        writer.writerow([f"# end of report for {vendor['vendor_id']}"] + [""] * (len(header) - 1))
        writer.writerow(["TOTAL", "", "", "", "footer", "", "", ""])


def main() -> None:
    if EXPORT_DIR.exists():
        for path in EXPORT_DIR.glob("*.csv"):
            path.unlink()
    for vendor in VENDORS:
        for file_index in range(1, 11):
            write_vendor_file(vendor, file_index)
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(yaml.safe_dump(vendor_profiles(), sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
