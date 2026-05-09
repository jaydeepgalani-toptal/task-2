#!/bin/bash
set -euo pipefail

cd /workspace

cat > modsync/versioning.py <<'PY'
from __future__ import annotations

import re
from collections.abc import Iterable

from packaging.version import Version

from .models import Attachment


_VERSION_RE = re.compile(r"-(\d+(?:\.\d+)*(?:[-\.]?(?:alpha|beta|rc|dev)\d*)?)\.zip$", re.IGNORECASE)


def extract_version(filename: str) -> Version:
    match = _VERSION_RE.search(filename)
    if not match:
        raise ValueError(f"missing version in {filename}")
    return Version(match.group(1))


def _normalize_constraints(constraints: str | Iterable[str]) -> list[str]:
    if isinstance(constraints, str):
        items = [constraints]
    else:
        items = list(constraints)
    return [item.strip() for item in items if item and item.strip()]


def in_constraint(version: Version, constraint: str) -> bool:
    raw = constraint.strip()
    if version.is_prerelease:
        return False
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
        base = Version(raw[:-2].lstrip("v").strip())
        upper = Version(f"{base.major}.{base.minor + 1}")
        return base <= version < upper
    if raw.lower().endswith("exactly"):
        base = Version(raw[:-7].strip().lstrip("v"))
        upper = Version(f"{base.major}.{base.minor + 1}")
        return base <= version < upper
    return version == Version(raw.lstrip("v"))


def select_best_attachment(attachments: list[Attachment], constraints: str | Iterable[str]) -> Attachment:
    active = _normalize_constraints(constraints)
    candidates = []
    for item in attachments:
        version = extract_version(item.filename)
        if all(in_constraint(version, constraint) for constraint in active):
            candidates.append(item)
    if not candidates:
        raise LookupError(f"no attachment satisfies {active!r}")
    return max(candidates, key=lambda item: extract_version(item.filename))
PY

cat > modsync/dependencies.py <<'PY'
from __future__ import annotations

import re

from .models import Attachment, Requirement, ThreadPage


_BULLET_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9 ]+?)\s+(?P<constraint>v?[0-9][0-9A-Za-z\.\+\-]*?(?:\s+only)?)$")
_REQUIRES_RE = re.compile(
    r"Requires\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+(?P<constraint>>=[^—]+)",
    re.IGNORECASE,
)
_BUILT_AGAINST_RE = re.compile(
    r"built against\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+v?(?P<constraint>\d+\.\d+\s+exactly)",
    re.IGNORECASE,
)
_PIN_RE = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+must be exactly\s+(?P<constraint>\d+(?:\.\d+)+)",
    re.IGNORECASE,
)
_LINUX_PIN_RE = re.compile(r"pin to (?P<version>\d+(?:\.\d+)+) if you're on Linux", re.IGNORECASE)


def _thread_mod_name(page: ThreadPage) -> str:
    head = page.title.split("—", 1)[0].strip()
    return re.sub(r"\s+\d+(?:\.\d+)*(?:\s+\w+)?$", "", head).strip()


def gather_posts(page: ThreadPage) -> list[str]:
    return [post.body_text for post in page.posts]


def find_requirements(page: ThreadPage) -> list[Requirement]:
    requirements: list[Requirement] = []
    thread_name = _thread_mod_name(page)
    for body in gather_posts(page):
        for raw_line in body.splitlines():
            line = " ".join(raw_line.split()).strip(" -")
            if not line:
                continue
            match = _BULLET_RE.match(line)
            if match:
                requirements.append(
                    Requirement(name=match.group("name"), constraint=match.group("constraint").replace(" only", ""))
                )
                continue
            match = _REQUIRES_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint").strip()))
                continue
            match = _BUILT_AGAINST_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint")))
                continue
            match = _PIN_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint")))
                continue
            match = _LINUX_PIN_RE.search(line)
            if match:
                requirements.append(Requirement(name=thread_name, constraint=match.group("version")))
    return requirements


def candidate_attachments(page: ThreadPage) -> list[Attachment]:
    prefix = f"{page.slug}-"
    filtered: list[Attachment] = []
    for item in page.attachments:
        name = item.filename.lower()
        badge = (item.badge or "").lower()
        if not name.endswith(".zip"):
            continue
        if not name.startswith(prefix):
            continue
        if any(token in name for token in ("source", "screenshots", "gallery", "texture", "music", "soundscape", "changelog")):
            continue
        if any(token in badge for token in ("optional", "companion", "source archive", "screenshots", "press kit")):
            continue
        filtered.append(item)
    return filtered
PY

cat > modsync/engine.py <<'PY'
from __future__ import annotations

from pathlib import Path

from .client import ForumClient
from .dependencies import candidate_attachments, find_requirements
from .scrape import choose_thread, extract_threads, parse_thread
from .versioning import select_best_attachment


def _find_page(client: ForumClient, target: str):
    search_threads = extract_threads(client.get_search(target), client.base_url)
    if not search_threads:
        search_threads = extract_threads(client.get_index(), client.base_url)
    ref = choose_thread(search_threads, target)
    return parse_thread(client.get_soup(ref.url), ref.url)


def download_target(forum_url: str, target: str, out_dir: Path) -> list[Path]:
    client = ForumClient(forum_url)
    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    written: set[str] = set()
    constraints: dict[str, list[str]] = {}
    seen: set[tuple[str, tuple[str, ...]]] = set()

    def resolve(name: str, incoming: str = "") -> None:
        if incoming:
            constraints.setdefault(name, [])
            if incoming not in constraints[name]:
                constraints[name].append(incoming)
        active = tuple(constraints.get(name, []))
        marker = (name, active)
        if marker in seen:
            return
        seen.add(marker)
        page = _find_page(client, name)
        selected = select_best_attachment(candidate_attachments(page), active)
        if selected.filename not in written:
            destination = out_dir / selected.filename
            client.download(selected.url, destination)
            written.add(selected.filename)
            downloaded.append(destination)
        for requirement in find_requirements(page):
            resolve(requirement.name, requirement.constraint)

    resolve(target)
    return downloaded
PY

rm -rf downloads
./bin/download-mods --forum-url "${FORUM_URL:-http://localhost:8080}" --target "Skyforge Overhaul" --out downloads/
