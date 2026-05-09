from __future__ import annotations

import re

from packaging.version import Version

from .models import Attachment


_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*(?:[-\.]?(?:alpha|beta|rc|dev)\d*)?)", re.IGNORECASE)


def extract_version(filename: str) -> Version:
    match = _VERSION_RE.search(filename)
    if not match:
        return Version("0")
    return Version(match.group(1))


def in_constraint(version: Version, constraint: str) -> bool:
    raw = constraint.strip()
    if not raw:
        return True
    if "," in raw:
        return all(in_constraint(version, part) for part in raw.split(","))
    if raw.startswith(">="):
        return version >= Version(raw[2:].strip())
    if raw.startswith("<"):
        return version < Version(raw[1:].strip())
    if raw.endswith("+"):
        return version >= Version(raw[:-1].lstrip("v").strip())
    if raw.lower().endswith(".x"):
        prefix = raw[:-2].lstrip("v").strip()
        return str(version).startswith(f"{prefix}.")
    if raw.lower().endswith("exactly"):
        value = raw[:-7].strip().lstrip("v")
        return version == Version(f"{value}.0")
    return version == Version(raw.lstrip("v"))


def select_best_attachment(attachments: list[Attachment], constraint: str) -> Attachment:
    candidates = [item for item in attachments if in_constraint(extract_version(item.filename), constraint)]
    if not candidates:
        raise LookupError(f"no attachment satisfies {constraint!r}")
    return max(candidates, key=lambda item: extract_version(item.filename))
