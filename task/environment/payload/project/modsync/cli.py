from __future__ import annotations

import argparse
from pathlib import Path

from .engine import download_target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download release archives for a mod thread")
    parser.add_argument("--forum-url", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    download_target(args.forum_url, args.target, Path(args.out))
    return 0
