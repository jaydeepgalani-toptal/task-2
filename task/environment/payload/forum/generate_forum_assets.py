from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from forum_seed import get_fixtures


def write_zip(path: Path, mod: str, version: str) -> None:
    content = f"mod: {mod}\nversion: {version}\ngenerated_for: vetto-task-rmd\n"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("MOD_INFO.txt", content)


def main() -> None:
    root = Path("/opt/localforum/fixtures")
    root.mkdir(parents=True, exist_ok=True)

    for name, fixture in get_fixtures().items():
        fixture_dir = root / name
        attachments_dir = fixture_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        for thread in fixture["threads"]:
            for item in thread["posts"]:
                for asset in item["attachments"]:
                    write_zip(attachments_dir / asset["filename"], asset["mod"], asset["version"])
        (fixture_dir / "forum.json").write_text(json.dumps(fixture, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
