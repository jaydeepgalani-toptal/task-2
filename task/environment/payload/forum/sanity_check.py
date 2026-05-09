from __future__ import annotations

import re
from html import unescape

from packaging.version import Version

from forum_seed import get_fixtures


def to_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "\n", fragment)
    return re.sub(r"\n+", "\n", unescape(text)).strip()


def version_from_filename(filename: str) -> Version:
    match = re.search(r"(\d+(?:\.\d+)*(?:[-\.]?(?:alpha|beta|rc|dev)\d*)?)", filename, re.IGNORECASE)
    if not match:
        return Version("0")
    return Version(match.group(1))


def broken_constraint(version: Version, constraint: str) -> bool:
    raw = constraint.strip()
    if not raw:
        return True
    if "," in raw:
        return all(broken_constraint(version, part) for part in raw.split(","))
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
        return version == Version(f"{raw[:-7].strip().lstrip('v')}.0")
    return version == Version(raw.lstrip("v"))


def correct_constraint(version: Version, constraint: str) -> bool:
    raw = constraint.strip()
    if not raw:
        return not version.is_prerelease
    if version.is_prerelease:
        return False
    if "," in raw:
        return all(correct_constraint(version, part) for part in raw.split(","))
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


def broken_requirements(thread: dict) -> list[tuple[str, str]]:
    body = to_text(thread["posts"][0]["body_html"])
    results: list[tuple[str, str]] = []
    for line in body.splitlines():
        line = " ".join(line.split()).strip(" -")
        if not line:
            continue
        bullet = re.match(r"^(?P<name>[A-Za-z][A-Za-z0-9 ]+?)\s+(?P<constraint>v?[0-9][0-9A-Za-z\.\+\-]*?(?:\s+only)?)$", line)
        if bullet:
            results.append((bullet.group("name"), bullet.group("constraint").replace(" only", "")))
            continue
        requires = re.search(r"Requires\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+(?P<constraint>>=[^—]+)", line, re.IGNORECASE)
        if requires:
            results.append((requires.group("name"), requires.group("constraint")))
            continue
        built = re.search(
            r"built against\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+v?(?P<constraint>\d+\.\d+\s+exactly)",
            line,
            re.IGNORECASE,
        )
        if built:
            results.append((built.group("name"), built.group("constraint")))
            continue
        pin = re.search(
            r"(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+must be exactly\s+(?P<constraint>\d+(?:\.\d+)+)",
            line,
            re.IGNORECASE,
        )
        if pin:
            results.append((pin.group("name"), pin.group("constraint")))
    return results


def correct_requirements(thread: dict) -> list[tuple[str, str]]:
    title_name = thread["title"].split("—", 1)[0].strip()
    results: list[tuple[str, str]] = []
    for post in thread["posts"]:
        body = to_text(post["body_html"])
        for line in body.splitlines():
            line = " ".join(line.split()).strip(" -")
            if not line:
                continue
            bullet = re.match(r"^(?P<name>[A-Za-z][A-Za-z0-9 ]+?)\s+(?P<constraint>v?[0-9][0-9A-Za-z\.\+\-]*?(?:\s+only)?)$", line)
            if bullet:
                results.append((bullet.group("name"), bullet.group("constraint").replace(" only", "")))
                continue
            requires = re.search(
                r"Requires\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+(?P<constraint>>=[^—]+)",
                line,
                re.IGNORECASE,
            )
            if requires:
                results.append((requires.group("name"), requires.group("constraint").strip()))
                continue
            built = re.search(
                r"built against\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+v?(?P<constraint>\d+\.\d+\s+exactly)",
                line,
                re.IGNORECASE,
            )
            if built:
                results.append((built.group("name"), built.group("constraint")))
                continue
            pin = re.search(
                r"(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+must be exactly\s+(?P<constraint>\d+(?:\.\d+)+)",
                line,
                re.IGNORECASE,
            )
            if pin:
                results.append((pin.group("name"), pin.group("constraint")))
                continue
            linux_pin = re.search(r"pin to (?P<version>\d+(?:\.\d+)+) if you're on Linux", line, re.IGNORECASE)
            if linux_pin:
                results.append((title_name, linux_pin.group("version")))
    return results


def thread_lookup(fixture: dict, name: str) -> dict:
    lowered = name.lower()
    choices = [item for item in fixture["threads"] if lowered in item["title"].lower()]
    choices.sort(key=lambda item: ("mirror" in item["title"].lower(), len(item["title"])))
    return choices[0]


def broken_candidates(thread: dict) -> list[dict]:
    attachments = []
    for post in thread["posts"]:
        attachments.extend(post["attachments"])
    return attachments


def correct_candidates(thread: dict) -> list[dict]:
    prefix = f"{thread['slug']}-"
    results = []
    for post in thread["posts"]:
        for item in post["attachments"]:
            name = item["filename"].lower()
            badge = (item.get("badge") or "").lower()
            if not name.endswith(".zip"):
                continue
            if not name.startswith(prefix):
                continue
            if any(token in name for token in ("source", "screenshot", "gallery", "texture", "music", "soundscape", "changelog")):
                continue
            if any(token in badge for token in ("optional", "companion", "source archive", "screenshots", "press kit")):
                continue
            results.append(item)
    return results


def choose(candidates: list[dict], constraints: list[str], predicate) -> str:
    allowed = []
    for item in candidates:
        version = version_from_filename(item["filename"])
        if all(predicate(version, constraint) for constraint in constraints):
            allowed.append(item)
    allowed.sort(key=lambda item: version_from_filename(item["filename"]))
    return allowed[-1]["filename"]


def solve_fixture(fixture: dict, requirement_reader, candidate_reader, predicate, combine: bool) -> set[str]:
    selected: set[str] = set()
    constraints: dict[str, list[str]] = {}
    seen: set[tuple[str, tuple[str, ...]]] = set()

    def resolve(name: str, incoming: str = "") -> None:
        if incoming:
            constraints.setdefault(name, []).append(incoming)
        active = tuple(constraints.get(name, [])) if combine else ((incoming,) if incoming else tuple())
        key = (name, active)
        if key in seen:
            return
        seen.add(key)
        thread = thread_lookup(fixture, name)
        candidates = candidate_reader(thread)
        if not combine and not active:
            selected.update(item["filename"] for item in candidates)
        else:
            selected.add(choose(candidates, list(active), predicate))
        for dep_name, dep_constraint in requirement_reader(thread):
            resolve(dep_name, dep_constraint)

    resolve("Skyforge Overhaul")
    return selected


def main() -> None:
    fixtures = get_fixtures()
    visible_correct = solve_fixture(fixtures["default"], correct_requirements, correct_candidates, correct_constraint, True)
    assert visible_correct == {
        "skyforge-overhaul-3.4.1.zip",
        "corelib-1.4.0.zip",
        "terrainkit-2.0.5.zip",
        "weatherhooks-0.9.8.zip",
        "scriptbridge-5.1.2.zip",
    }
    visible_broken = solve_fixture(fixtures["default"], broken_requirements, broken_candidates, broken_constraint, False)
    assert "corelib-1.5.0-beta2.zip" in visible_broken
    assert "scriptbridge-5.1.0.zip" in visible_broken
    assert "skyforge-overhaul-3.5.0-rc1.zip" in visible_broken
    assert "skyforge-hd-textures-1.0.zip" in visible_broken
    assert "skyforge-screenshots.zip" in visible_broken
    assert "skyforge-overhaul-3.4.1.zip" in visible_correct

    hidden_correct = solve_fixture(fixtures["hidden"], correct_requirements, correct_candidates, correct_constraint, True)
    assert hidden_correct == {
        "skyforge-overhaul-4.0.2.zip",
        "corelib-2.2.1.zip",
        "terrainkit-3.3.7.zip",
        "weatherhooks-1.8.6.zip",
        "scriptbridge-6.4.1.zip",
    }
    hidden_broken = solve_fixture(fixtures["hidden"], broken_requirements, broken_candidates, broken_constraint, False)
    assert "corelib-2.3.0-beta1.zip" in hidden_broken
    assert "scriptbridge-6.4.0.zip" in hidden_broken
    assert hidden_broken != hidden_correct


if __name__ == "__main__":
    main()
