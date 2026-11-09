# URL fetch — turn "a repo, a post" into documents the engine can ingest.
# Stdlib only (no extra dependency). Disclosed in README per catalog rule 13.
# Safety: http/https only, size cap, redirects followed, hard timeout.
#
# A GitHub *repo* URL is special-cased: the repo landing page is navigation
# chrome, so we fetch the README from raw.githubusercontent.com instead. That is
# the difference between a grounded review and one built on "Skip to content".

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import List

from .models import Document, DocumentType

MAX_BYTES = 200_000          # 200KB cap — a blog post or README, not a 50MB dump
TIMEOUT_S = 20
_UA = "hermes-upfront/0.2 (+https://github.com/NousResearch/hermes-agent)"

_HTML_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\n{3,}")
_LINE_WS = re.compile(r"[ \t]+")

_GITHUB_REPO = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s?#]+)/?$")

# Navigation / boilerplate lines that carry no content but pollute extraction.
_CHROME_PREFIXES = (
    "Skip to content", "You signed in", "You signed out", "Sign in", "Sign up",
    "Sign out", "Navigation Menu", "Search or jump to", "Search code", "Search",
    "Reload to refresh", "Dismiss alert", "Footer", "Terms", "Privacy", "Security",
    "Status", "Docs", "Contact", "Manage cookies", "Accept all", "Reject all",
    "Provide feedback", "Copy path", "Blame", "Raw", "Latest commit", "History",
    "Branches", "Tags", "Contributors", "About", "Releases", "Packages", "Languages",
    "Watchers", "Forks", "Stars", "Go to file", "Code", "Issues", "Pull requests",
    "Actions", "Projects", "Wiki", "Insights", "Settings",
)


def _get_text(url: str) -> str | None:
    """Fetch a URL and return decoded, chrome-stripped text. None on any failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read(MAX_BYTES + 1)
            ctype = (resp.headers.get("Content-Type") or "").lower()
    except Exception:
        return None
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
    text = raw.decode("utf-8", errors="ignore")
    if "html" in ctype or text.lstrip().startswith("<"):
        text = _html_to_text(text)
    return _clean(text)


def fetch_url(url: str, doc_type: DocumentType = DocumentType.CONTEXT) -> Document | None:
    """Fetch a URL and return it as a Document, or None on any failure.
    Never raises — a bad URL should not kill the simulation."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return None

    m = _GITHUB_REPO.match(url)
    if m:
        owner, repo = m.group(1), m.group(2)
        for branch in ("HEAD", "main", "master"):
            readme = _get_text(
                f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            )
            if readme:
                return Document(type=doc_type, content=readme, source=url)

    text = _get_text(url)
    if not text:
        return None
    return Document(type=doc_type, content=text, source=url)


def fetch_urls(urls: List[str]) -> List[Document]:
    out: List[Document] = []
    for u in urls or []:
        d = fetch_url(u)
        if d is not None:
            out.append(d)
    return out


def _html_to_text(html: str) -> str:
    html = _HTML_RE.sub("\n", html)      # drop script/style bodies
    html = _TAG_RE.sub(" ", html)        # strip tags
    return html


def _drop_chrome(text: str) -> str:
    keep = []
    for ln in text.splitlines():
        stripped = ln.strip()
        if not stripped:
            keep.append("")
            continue
        if any(stripped.startswith(p) for p in _CHROME_PREFIXES):
            continue
        keep.append(stripped)
    return _WS_RE.sub("\n\n", "\n".join(keep)).strip()


def _clean(text: str) -> str:
    lines = [_LINE_WS.sub(" ", ln).strip() for ln in text.splitlines()]
    text = "\n".join(lines)
    text = _WS_RE.sub("\n\n", text)
    return _drop_chrome(text)[:50_000]  # cap the text the engine ingests
