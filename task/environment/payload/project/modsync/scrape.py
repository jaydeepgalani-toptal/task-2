from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Attachment, Post, ThreadPage, ThreadRef


def slugify_name(name: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return lowered


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def extract_threads(index_soup: BeautifulSoup, base_url: str) -> list[ThreadRef]:
    threads: list[ThreadRef] = []
    for anchor in index_soup.select("a.thread-link"):
        href = anchor.get("href")
        if not href:
            continue
        threads.append(ThreadRef(title=anchor.get_text(" ", strip=True), url=urljoin(base_url, href)))
    return threads


def choose_thread(threads: list[ThreadRef], target: str) -> ThreadRef:
    target_norm = normalize_title(target)
    scored: list[tuple[int, ThreadRef]] = []
    for ref in threads:
        title_norm = normalize_title(ref.title)
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
        scored.append((score, ref))
    if not scored:
        raise LookupError(f"could not find thread for {target!r}")
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def parse_thread(thread_soup: BeautifulSoup, url: str) -> ThreadPage:
    title_node = thread_soup.select_one("h1.thread-title")
    if title_node is None:
        raise ValueError("thread title missing")
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    page = ThreadPage(title=title_node.get_text(" ", strip=True), slug=slug, url=url)
    for article in thread_soup.select("article.post"):
        author = article.get("data-author", "unknown")
        pinned = "pinned" in article.get("class", [])
        body = article.select_one(".post-body")
        body_text = body.get_text("\n", strip=True) if body else ""
        page.posts.append(Post(author=author, body_text=body_text, pinned=pinned))
        for link in article.select("ul.attachments a[href$='.zip']"):
            href = link.get("href")
            if not href:
                continue
            badge_node = link.find_next_sibling("span", class_="badge")
            badge = badge_node.get_text(" ", strip=True) if badge_node else None
            page.attachments.append(
                Attachment(
                    filename=link.get_text(" ", strip=True),
                    url=urljoin(url, href),
                    badge=badge,
                )
            )
    return page
