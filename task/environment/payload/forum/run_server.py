from __future__ import annotations

import html
import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path("/opt/localforum/fixtures")
ACTIVE_FIXTURE = os.environ.get("FORUM_FIXTURE", "default")


def fixture_dir() -> Path:
    return ROOT / ACTIVE_FIXTURE


def load_fixture() -> dict:
    with (fixture_dir() / "forum.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def plain_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def render_layout(title: str, body: str) -> bytes:
    page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: sans-serif; margin: 0; background: #f4f1ea; color: #1e1e1e; }}
      header {{ background: #2c3c46; color: #fff; padding: 1rem 1.5rem; }}
      main {{ max-width: 960px; margin: 0 auto; padding: 1.5rem; }}
      a {{ color: #0f4c81; text-decoration: none; }}
      .thread-list, .attachments {{ list-style: none; padding: 0; }}
      .thread-list li, article.post {{ background: #fff; border: 1px solid #d7d0c5; margin-bottom: 1rem; padding: 1rem; }}
      .meta {{ color: #5d5d5d; font-size: 0.92rem; margin-top: 0.25rem; }}
      .badge {{ display: inline-block; margin-left: 0.4rem; padding: 0.08rem 0.45rem; background: #eadcb8; border-radius: 999px; font-size: 0.8rem; }}
      article.post.pinned {{ border-left: 4px solid #996515; }}
      .post-header {{ margin-bottom: 0.75rem; font-weight: 600; }}
      .post-body p, .post-body ul {{ margin-top: 0; }}
      .attachments li {{ margin-bottom: 0.4rem; }}
      nav {{ margin-bottom: 1rem; }}
      input[type=text] {{ width: 18rem; padding: 0.35rem; }}
    </style>
  </head>
  <body>
    <header><strong>Northwind Mods Forum</strong></header>
    <main>
      <nav>
        <a href="/">Index</a>
        <form action="/search" method="get" style="display:inline; margin-left: 1rem;">
          <input type="text" name="q" placeholder="Search threads">
        </form>
      </nav>
      {body}
    </main>
  </body>
</html>
"""
    return page.encode("utf-8")


class ForumHandler(BaseHTTPRequestHandler):
    server_version = "NorthwindForum/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.serve_index()
            return
        if parsed.path.startswith("/thread/"):
            self.serve_thread(parsed.path.rsplit("/", 1)[-1])
            return
        if parsed.path.startswith("/attachments/"):
            self.serve_attachment(parsed.path.rsplit("/", 1)[-1])
            return
        if parsed.path == "/search":
            term = parse_qs(parsed.query).get("q", [""])[0]
            self.serve_search(term)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def serve_index(self) -> None:
        fixture = load_fixture()
        threads = sorted(fixture["threads"], key=lambda item: item["title"].lower())
        items = []
        for thread in threads:
            op = thread["posts"][0]
            title_html = thread.get("title_html") or html.escape(thread["title"])
            items.append(
                f"""
                <li>
                  <a class="thread-link" href="/thread/{thread['slug']}">{title_html}</a>
                  <div class="meta">by {html.escape(op['author'])} on {html.escape(op['posted'])}</div>
                </li>
                """
            )
        body = "<h1>Forum Index</h1><ul class=\"thread-list\">" + "".join(items) + "</ul>"
        self.respond_html("Forum Index", body)

    def serve_thread(self, slug: str) -> None:
        fixture = load_fixture()
        thread = next((item for item in fixture["threads"] if item["slug"] == slug), None)
        if thread is None:
            self.send_error(HTTPStatus.NOT_FOUND, "thread not found")
            return
        articles = []
        for item in thread["posts"]:
            badge = " <span class=\"badge\">PINNED</span>" if item["kind"] == "pinned" else ""
            attachments_html = ""
            if item["attachments"]:
                links = []
                for asset in item["attachments"]:
                    badge_html = f" <span class=\"badge\">{html.escape(asset['badge'])}</span>" if asset.get("badge") else ""
                    links.append(
                        f"<li><a href=\"/attachments/{html.escape(asset['filename'])}\">{html.escape(asset['filename'])}</a>{badge_html}</li>"
                    )
                attachments_html = "<ul class=\"attachments\">" + "".join(links) + "</ul>"
            article_class = "post" + (" pinned" if item["kind"] == "pinned" else "")
            articles.append(
                f"""
                <article class="{article_class}" data-author="{html.escape(item['author'])}">
                  <div class="post-header">{html.escape(item['author'])} • {html.escape(item['posted'])}{badge}</div>
                  <div class="post-body">{item['body_html']}</div>
                  {attachments_html}
                </article>
                """
            )
        title_html = thread.get("title_html") or html.escape(thread["title"])
        body = f"<h1 class=\"thread-title\">{title_html}</h1>" + "".join(articles)
        self.respond_html(thread["title"], body)

    def serve_attachment(self, filename: str) -> None:
        path = fixture_dir() / "attachments" / filename
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "attachment not found")
            return
        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_search(self, term: str) -> None:
        needle = term.strip().lower()
        fixture = load_fixture()
        matches = []
        for thread in fixture["threads"]:
            op_text = plain_text(thread["posts"][0]["body_html"]).lower()
            if needle and needle not in thread["title"].lower() and needle not in op_text:
                continue
            matches.append(thread)
        matches.sort(key=lambda item: item["title"].lower())
        items = []
        for thread in matches:
            items.append(
                f"<li><a class=\"thread-link\" href=\"/thread/{thread['slug']}\">{html.escape(thread['title'])}</a></li>"
            )
        body = f"<h1>Search</h1><p>Results for {html.escape(term)!r}</p><ul class=\"thread-list\">{''.join(items)}</ul>"
        self.respond_html("Search", body)

    def respond_html(self, title: str, body: str) -> None:
        payload = render_layout(title, body)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8080), ForumHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
