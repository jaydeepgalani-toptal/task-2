from __future__ import annotations

from pathlib import Path

from .client import ForumClient
from .dependencies import candidate_attachments, find_requirements
from .scrape import choose_thread, extract_threads, parse_thread
from .versioning import select_best_attachment


def _find_page(client: ForumClient, target: str):
    threads = extract_threads(client.get_index(), client.base_url)
    ref = choose_thread(threads, target)
    return parse_thread(client.get_soup(ref.url), ref.url)


def download_target(forum_url: str, target: str, out_dir: Path) -> list[Path]:
    client = ForumClient(forum_url)
    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    seen: set[str] = set()

    def resolve(name: str, constraint: str = "") -> None:
        page = _find_page(client, name)
        candidates = candidate_attachments(page)
        if not constraint:
            for item in candidates:
                if item.filename in seen:
                    continue
                destination = out_dir / item.filename
                client.download(item.url, destination)
                seen.add(item.filename)
                downloaded.append(destination)
        else:
            selected = select_best_attachment(candidates, constraint)
            if selected.filename not in seen:
                destination = out_dir / selected.filename
                client.download(selected.url, destination)
                seen.add(selected.filename)
                downloaded.append(destination)
        for requirement in find_requirements(page):
            resolve(requirement.name, requirement.constraint)

    resolve(target)
    return downloaded
