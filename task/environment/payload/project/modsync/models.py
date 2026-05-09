from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThreadRef:
    title: str
    url: str


@dataclass(frozen=True)
class Attachment:
    filename: str
    url: str
    badge: str | None = None


@dataclass(frozen=True)
class Post:
    author: str
    body_text: str
    pinned: bool = False


@dataclass
class ThreadPage:
    title: str
    slug: str
    url: str
    posts: list[Post] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass(frozen=True)
class Requirement:
    name: str
    constraint: str

