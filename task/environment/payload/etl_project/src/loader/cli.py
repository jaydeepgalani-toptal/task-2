from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_load


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize vendor shipment ledgers")
    parser.add_argument("--in", dest="input_dir", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_load(Path(args.input_dir), Path(args.profiles), Path(args.out))
    return 0
