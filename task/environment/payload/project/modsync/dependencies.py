from __future__ import annotations

import re

from .models import Attachment, Requirement, ThreadPage


_BULLET_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9 ]+?)\s+(?P<constraint>v?[0-9][0-9A-Za-z\.\+\-]*?(?:\s+only)?)$")
_REQUIRES_RE = re.compile(
    r"Requires\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+(?P<constraint>>=[^\.]+)",
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


def gather_posts(page: ThreadPage) -> list[str]:
    if not page.posts:
        return []
    return [page.posts[0].body_text]


def find_requirements(page: ThreadPage) -> list[Requirement]:
    requirements: list[Requirement] = []
    for body in gather_posts(page):
        for raw_line in body.splitlines():
            line = " ".join(raw_line.split()).strip(" -")
            if not line:
                continue
            match = _BULLET_RE.match(line)
            if match:
                constraint = match.group("constraint").replace(" only", "")
                requirements.append(Requirement(name=match.group("name"), constraint=constraint))
                continue
            match = _REQUIRES_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint")))
                continue
            match = _BUILT_AGAINST_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint")))
                continue
            match = _PIN_RE.search(line)
            if match:
                requirements.append(Requirement(name=match.group("name"), constraint=match.group("constraint")))
    return requirements


def candidate_attachments(page: ThreadPage) -> list[Attachment]:
    return [item for item in page.attachments if item.filename.lower().endswith(".zip")]
