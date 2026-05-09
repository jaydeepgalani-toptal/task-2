from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import pytest
import requests
from bs4 import BeautifulSoup
from packaging.version import Version


ROOT = Path("/workspace")
DOWNLOADS = ROOT / "downloads"
FORUM_URL = os.environ.get("FORUM_URL", "http://localhost:8080")
TARGET = "Skyforge Overhaul"
VISIBLE_EXPECTED = {
    "skyforge-overhaul-3.4.1.zip",
    "corelib-1.4.0.zip",
    "terrainkit-2.0.5.zip",
    "weatherhooks-0.9.8.zip",
    "scriptbridge-5.1.2.zip",
}
OPTIONAL_VISIBLE = {
    "skyforge-hd-textures-1.0.zip",
    "skyforge-music-pack-2.1.zip",
    "skyforge-overhaul-3.4.1-source.zip",
    "skyforge-screenshots.zip",
    "vaultcopy-330.zip",
    "frostbite-tweaks-1.9.0.zip",
    "wildlands-photo-pack-2026.zip",
}
BAD_NAME_RE = re.compile(r"(alpha|beta|rc|dev|texture|music|source|screenshot|gallery|changelog)", re.IGNORECASE)
VERSION_RE = re.compile(r"-(\d+(?:\.\d+)*(?:[-\.]?(?:alpha|beta|rc|dev)\d*)?)\.zip$", re.IGNORECASE)


@dataclass(frozen=True)
class Attachment:
    filename: str
    url: str
    badge: str | None


@dataclass(frozen=True)
class Post:
    body_text: str
    pinned: bool


@dataclass
class ThreadPage:
    title: str
    slug: str
    url: str
    posts: list[Post]
    attachments: list[Attachment]

    @property
    def mod_name(self) -> str:
        head = self.title.split("—", 1)[0].strip()
        return re.sub(r"\s+\d+(?:\.\d+)*(?:\s+\w+)?$", "", head).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def attachment_hash(filename: str, fixture: str) -> str:
    ensure_server(fixture)
    response = requests.get(urljoin(FORUM_URL + "/", f"attachments/{filename}"), timeout=20)
    response.raise_for_status()
    return hashlib.sha256(response.content).hexdigest()


def ensure_server(fixture: str) -> None:
    subprocess.run(["forum-serverctl", "restart", fixture], check=True, cwd=ROOT)


def run_downloader(fixture: str) -> dict[str, str]:
    ensure_server(fixture)
    shutil.rmtree(DOWNLOADS, ignore_errors=True)
    env = os.environ.copy()
    env["FORUM_URL"] = FORUM_URL
    env["FORUM_FIXTURE"] = fixture
    subprocess.run(
        ["./bin/download-mods", "--forum-url", FORUM_URL, "--target", TARGET, "--out", "downloads/"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    return collect_downloads()


def collect_downloads() -> dict[str, str]:
    if not DOWNLOADS.exists():
        return {}
    outputs: dict[str, str] = {}
    for path in sorted(DOWNLOADS.glob("*.zip")):
        outputs[path.name] = sha256(path)
    return outputs


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def extract_threads(index_soup: BeautifulSoup) -> list[tuple[str, str]]:
    return [
        (anchor.get_text(" ", strip=True), urljoin(FORUM_URL + "/", anchor.get("href")))
        for anchor in index_soup.select("a.thread-link")
        if anchor.get("href")
    ]


def choose_thread(threads: list[tuple[str, str]], target: str) -> tuple[str, str]:
    target_norm = normalize(target)
    scored: list[tuple[int, tuple[str, str]]] = []
    for title, url in threads:
        title_norm = normalize(title)
        if target_norm not in title_norm:
            continue
        score = 0
        if title_norm.startswith(target_norm):
            score += 20
        if "stable release" in title_norm:
            score += 10
        if "mirror" not in title_norm:
            score += 5
        else:
            score -= 20
        if "superseded" not in title_norm:
            score += 5
        score -= abs(len(title_norm) - len(target_norm))
        scored.append((score, (title, url)))
    if not scored:
        raise AssertionError(f"no thread match for {target!r}")
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def fetch_search_threads(term: str) -> list[tuple[str, str]]:
    response = requests.get(urljoin(FORUM_URL + "/", "search"), params={"q": term}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return extract_threads(soup)


def parse_thread(url: str) -> ThreadPage:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title_node = soup.select_one("h1.thread-title")
    assert title_node is not None, f"missing title on {url}"
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    posts: list[Post] = []
    attachments: list[Attachment] = []
    for article in soup.select("article.post"):
        body = article.select_one(".post-body")
        posts.append(
            Post(
                body_text=body.get_text("\n", strip=True) if body else "",
                pinned="pinned" in article.get("class", []),
            )
        )
        for link in article.select("ul.attachments a[href$='.zip']"):
            href = link.get("href")
            if not href:
                continue
            badge_node = link.find_next_sibling("span", class_="badge")
            attachments.append(
                Attachment(
                    filename=link.get_text(" ", strip=True),
                    url=urljoin(url, href),
                    badge=badge_node.get_text(" ", strip=True) if badge_node else None,
                )
            )
    return ThreadPage(title=title_node.get_text(" ", strip=True), slug=slug, url=url, posts=posts, attachments=attachments)


def find_thread(name: str) -> ThreadPage:
    results = fetch_search_threads(name)
    if not results:
        index = requests.get(FORUM_URL, timeout=20)
        index.raise_for_status()
        results = extract_threads(BeautifulSoup(index.text, "html.parser"))
    _, url = choose_thread(results, name)
    return parse_thread(url)


def parse_requirements(page: ThreadPage) -> list[tuple[str, str]]:
    bullet_re = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9 ]+?)\s+(?P<constraint>v?[0-9][0-9A-Za-z\.\+\-]*?(?:\s+only)?)$")
    requires_re = re.compile(r"Requires\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+(?P<constraint>>=[^—]+)", re.IGNORECASE)
    built_re = re.compile(
        r"built against\s+(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+v?(?P<constraint>\d+\.\d+\s+exactly)",
        re.IGNORECASE,
    )
    must_re = re.compile(
        r"(?P<name>[A-Za-z][A-Za-z0-9 ]+)\s+must be exactly\s+(?P<constraint>\d+(?:\.\d+)+)",
        re.IGNORECASE,
    )
    linux_pin_re = re.compile(r"pin to (?P<version>\d+(?:\.\d+)+) if you're on Linux", re.IGNORECASE)

    requirements: list[tuple[str, str]] = []
    for post in page.posts:
        for raw_line in post.body_text.splitlines():
            line = " ".join(raw_line.split()).strip(" -")
            if not line:
                continue
            match = bullet_re.match(line)
            if match:
                requirements.append((match.group("name"), match.group("constraint").replace(" only", "")))
                continue
            match = requires_re.search(line)
            if match:
                requirements.append((match.group("name"), match.group("constraint").strip()))
                continue
            match = built_re.search(line)
            if match:
                requirements.append((match.group("name"), match.group("constraint")))
                continue
            match = must_re.search(line)
            if match:
                requirements.append((match.group("name"), match.group("constraint")))
                continue
            match = linux_pin_re.search(line)
            if match:
                requirements.append((page.mod_name, match.group("version")))
    return requirements


def extract_version(filename: str) -> Version:
    match = VERSION_RE.search(filename)
    if not match:
        raise AssertionError(f"could not extract version from {filename}")
    return Version(match.group(1))


def satisfies(version: Version, constraint: str) -> bool:
    raw = constraint.strip()
    if version.is_prerelease:
        return False
    if not raw:
        return True
    if "," in raw:
        return all(satisfies(version, part) for part in raw.split(","))
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


def release_candidates(page: ThreadPage) -> list[Attachment]:
    prefix = f"{page.slug}-"
    candidates: list[Attachment] = []
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
        candidates.append(item)
    return candidates


def resolve_expected() -> set[str]:
    resolved: dict[str, str] = {}
    constraints: dict[str, list[str]] = {}
    seen: set[tuple[str, tuple[str, ...]]] = set()

    def resolve(name: str, incoming: str = "") -> None:
        if incoming:
            constraints.setdefault(name, []).append(incoming)
        active = tuple(constraints.get(name, []))
        marker = (name, active)
        if marker in seen:
            return
        seen.add(marker)
        page = find_thread(name)
        allowed = []
        for item in release_candidates(page):
            version = extract_version(item.filename)
            if all(satisfies(version, constraint) for constraint in active):
                allowed.append(item)
        assert allowed, f"no release candidates for {name} with {active}"
        allowed.sort(key=lambda item: extract_version(item.filename))
        resolved[name] = allowed[-1].filename
        for dep_name, dep_constraint in parse_requirements(page):
            resolve(dep_name, dep_constraint)

    resolve(TARGET)
    return set(resolved.values())


def read_protected_hashes() -> dict[str, str]:
    path = Path("/opt/localforum/protected_hashes.json")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def phase_results() -> dict[str, object]:
    visible_run = run_downloader("default")
    visible_repeat = run_downloader("default")
    hidden_run = run_downloader("hidden")
    hidden_expected = resolve_expected()
    return {
        "visible": visible_run,
        "visible_repeat": visible_repeat,
        "hidden": hidden_run,
        "visible_hashes": {name: attachment_hash(name, "default") for name in visible_run},
        "hidden_expected": hidden_expected,
        "hidden_hashes": {name: attachment_hash(name, "hidden") for name in hidden_expected},
        "protected_hashes": read_protected_hashes(),
    }


def test_1_downloads_directory_exists_and_is_non_empty(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    assert DOWNLOADS.exists()
    assert visible


def test_2_visible_fixture_exact_zip_set(phase_results: dict[str, object]) -> None:
    visible = set(phase_results["visible"].keys())
    assert visible == VISIBLE_EXPECTED


def test_3_visible_hashes_match_attachment_bytes(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    visible_hashes = phase_results["visible_hashes"]
    for filename in VISIBLE_EXPECTED:
        assert visible[filename] == visible_hashes[filename]


def test_4_corelib_visible_selection(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    assert visible["corelib-1.4.0.zip"] == phase_results["visible_hashes"]["corelib-1.4.0.zip"]


def test_5_terrainkit_visible_selection(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    assert visible["terrainkit-2.0.5.zip"] == phase_results["visible_hashes"]["terrainkit-2.0.5.zip"]


def test_6_weatherhooks_visible_selection(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    assert visible["weatherhooks-0.9.8.zip"] == phase_results["visible_hashes"]["weatherhooks-0.9.8.zip"]


def test_7_scriptbridge_visible_selection(phase_results: dict[str, object]) -> None:
    visible = phase_results["visible"]
    assert visible["scriptbridge-5.1.2.zip"] == phase_results["visible_hashes"]["scriptbridge-5.1.2.zip"]


def test_8_no_prerelease_zip_names_present(phase_results: dict[str, object]) -> None:
    visible_names = set(phase_results["visible"].keys())
    assert all(re.search(r"(alpha|beta|rc|dev)", name, re.IGNORECASE) is None for name in visible_names)


def test_9_optional_and_non_release_archives_are_absent(phase_results: dict[str, object]) -> None:
    visible_names = set(phase_results["visible"].keys())
    assert visible_names.isdisjoint(OPTIONAL_VISIBLE)
    assert all(BAD_NAME_RE.search(name) is None for name in visible_names)


def test_10_second_clean_visible_run_is_deterministic(phase_results: dict[str, object]) -> None:
    visible = set(phase_results["visible"].keys())
    repeat = set(phase_results["visible_repeat"].keys())
    assert repeat == visible


def test_11_hidden_fixture_output_matches_hidden_expected_set_and_hashes(phase_results: dict[str, object]) -> None:
    hidden = phase_results["hidden"]
    hidden_expected = phase_results["hidden_expected"]
    hidden_hashes = phase_results["hidden_hashes"]
    assert set(hidden.keys()) == hidden_expected
    for filename in hidden_expected:
        assert hidden[filename] == hidden_hashes[filename]


def test_12_protected_files_unchanged(phase_results: dict[str, object]) -> None:
    protected_hashes: dict[str, str] = phase_results["protected_hashes"]
    for raw_path, expected_hash in protected_hashes.items():
        path = Path(raw_path)
        assert path.exists(), f"protected file missing: {path}"
        assert sha256(path) == expected_hash, f"protected file changed: {path}"
