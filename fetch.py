# URL fetch — turn "a repo, a post" into documents the engine can ingest.
# Stdlib only (no extra dependency). Disclosed in README per catalog rule 13.
# Safety: http/https only, size cap, redirects followed, hard timeout.
#
# A GitHub *repo* URL is special-cased: the repo landing page is navigation
# chrome, so we fetch the README from raw.githubusercontent.com instead. That is
# the difference between a grounded review and one built on "Skip to content".

from __future__ import annotations

import html
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import List

from .models import Document, DocumentType

MAX_BYTES = 2_000_000        # 2MB cap. Was 200KB: a real Next.js post is 1.66MB of
                             # inline SVG badges *before* the first sentence, so the old
                             # cap read the <head> and a pile of path coordinates and
                             # never reached the article. Cap the *prose* below, not
                             # the page before we have found it.
TIMEOUT_S = 20
_UA = "hermes-strategic-arena/0.6 (+https://github.com/NousResearch/hermes-agent)"

# <svg> blocks are geometry, not text: an icon set is thousands of path
# coordinates that survive tag-stripping as prose-shaped junk.
_SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.DOTALL | re.IGNORECASE)
_HTML_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\n{3,}")
_LINE_WS = re.compile(r"[ \t]+")

# A page must yield this many characters of prose before we treat it as a
# document. Measured on the real failure: the Arete page yields 9,210 prose
# chars once SVG is stripped, a junk page yields ~20. 150 sits an order of
# magnitude clear of both. Below it we return None, so the run is honestly
# degraded rather than reviewed off a title tag.
PROSE_MIN = 150

_GITHUB_REPO = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s?#]+)/?$")

# arXiv serves the same paper three ways, and only two of them are text. /pdf/
# returns raw PDF bytes; decoding those as UTF-8 yields a page of compressed
# stream noise that is *full of word-shaped tokens*, so it sails past the prose
# gate and the model gets binary as its "paper". That is worse than failing.
# Rewrite to the HTML full text, then the abstract page.
_ARXIV_RE = re.compile(r"^https?://(?:www\.|export\.)?arxiv\.org/(?:abs|pdf|html)/([^?#\s]+?)(?:\.pdf)?/?$")

# What any other PDF looks like from the outside. We cannot read a generic PDF
# without a dependency, and this plugin declares none — so say so, rather than
# feed the model bytes and call it a document.
_BINARY_MAGIC = (b"%PDF", b"PK\x03\x04", b"\x89PNG", b"GIF8", b"\xff\xd8")


# Links that were dropped, with the reason. The run reports them instead of
# quietly reviewing a smaller pile of documents than the user handed in.
LAST_SKIPPED: List[tuple] = []

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
    # long AI-written posts are mostly the argument wrapped in the same eight
    # blocks; they survive tag-stripping and sit exactly where the head window
    # wants to read the claim
    "Subscribe", "Sign up for", "Join our", "Newsletter", "Share this",
    "Read more", "Related posts", "You might also", "Follow us", "Cookie",
    "We use cookies", "Accept cookies", "This site uses", "Advertisement",
    "Sponsored", "Table of contents", "In this article", "Key takeaways",
    "TL;DR", "Leave a comment", "Comments (", "Back to top", "Load more",
)


# ── the address guard ─────────────────────────────────────────────────
# A URL the model chose is untrusted input. urllib would happily follow it to
# 127.0.0.1, a LAN host, or 169.254.169.254 (cloud metadata, which hands back
# the machine's own credentials), and the fetched text comes back to the model
# — so a prompt-injected page could turn a run into an internal port scan. The
# rule is simple: resolve the host and refuse anything that is not a global
# address. Requiring *every* address a name resolves to be global closes the
# multi-A-record case; re-checking each redirect hop closes the "public page
# redirects into the LAN" case.
#
# Known limit: this resolves the name and urllib resolves it again to connect,
# so a host that answers two different ways could in principle slip between the
# two lookups (a DNS-rebinding window). Pinning the resolved address would close
# it and needs a custom HTTPConnection; that is a follow-up, not a reason to
# leave the hole open. It is disclosed in the PR comment.

_REFUSED_REASON = ("refused: not a public http/https address (loopback, private, "
                   "link-local, CGNAT, unspecified and cloud-metadata targets are "
                   "never fetched)")


class _Refused(Exception):
    """A URL or redirect target was refused by the address guard."""


def _host_is_public(host: str) -> bool:
    """True only when every address `host` resolves to is a global address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (OSError, UnicodeError):
        return False
    if not infos:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


def _url_is_public(url: str) -> bool:
    """http/https only, and the host must resolve to global address(es) only."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    return _host_is_public(host)


class _PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-check every redirect target; refuse one that is not a public address."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _url_is_public(newurl):
            raise _Refused(f"refused: redirect to a non-public address ({newurl})")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_PublicRedirectHandler())


def _get_text(url: str) -> str | None:
    """Fetch a URL and return decoded, chrome-stripped text. None on any failure.

    Refuses a URL whose host is not a global address *before* any bytes are
    requested. The opener re-checks every redirect hop, so a public page cannot
    bounce the fetch into the LAN.
    """
    if not _url_is_public(url):
        LAST_SKIPPED.append((url, _REFUSED_REASON))
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with _OPENER.open(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read(MAX_BYTES + 1)
            ctype = (resp.headers.get("Content-Type") or "").lower()
    except _Refused as exc:
        LAST_SKIPPED.append((url, str(exc)))
        return None
    except Exception:
        return None
    if len(raw) > MAX_BYTES:
        raw = raw[:MAX_BYTES]
    return _extract_text(raw, ctype)


def _is_binary(raw: bytes, ctype: str) -> bool:
    if any(t in ctype for t in ("pdf", "octet-stream", "zip", "image/", "msword")):
        return True
    return any(raw.startswith(m) for m in _BINARY_MAGIC)


def _extract_text(raw: bytes, ctype: str = "") -> str | None:
    """bytes -> text a model can read, or None when the page yields no prose.

    Truncation happens *before* extraction only to bound memory; the real gate
    is PROSE_MIN below, so a page whose body sits behind 1.5MB of inline SVG is
    still read in full instead of being graded off its <head>.
    """
    if _is_binary(raw, ctype):
        return None
    text = raw.decode("utf-8", errors="ignore")
    if "html" in ctype or text.lstrip().startswith("<"):
        text = _html_to_text(text)
    text = _clean(text)
    if _prose_chars(text) < PROSE_MIN:
        return None
    return text


_COORD_RE = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9\.\-,;]+$")


def _prose_chars(text: str) -> int:
    """Characters in words that are actually words.

    SVG path coordinates (`M178.187`, `21.8099C9.76`) parse as tokens but carry
    no meaning; counting them as text is how a page of geometry passes for a
    document.
    """
    total = 0
    for w in text.split():
        if len(w) < 3 or _COORD_RE.match(w):
            continue
        if sum(c.isalpha() for c in w) / len(w) >= 0.6:
            total += len(w)
    return total


def fetch_url(url: str, doc_type: DocumentType = DocumentType.CONTEXT) -> Document | None:
    """Fetch a URL and return it as a Document, or None on any failure.
    Never raises — a bad URL should not kill the simulation."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return None

    arxiv = _ARXIV_RE.match(url)
    if arxiv:
        # full text first (arxiv's HTML rendering), then the abstract page. Both
        # are real text; the /pdf/ link the user pasted is not.
        ident = arxiv.group(1)
        for candidate in (f"https://arxiv.org/html/{ident}",
                          f"https://arxiv.org/abs/{ident}"):
            text = _get_text(candidate)
            if text:
                return Document(type=doc_type, content=text, source=url)
        LAST_SKIPPED.append((url, "arXiv did not serve a readable version of this paper"))
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
        if not any(u == url for u, _ in LAST_SKIPPED):
            LAST_SKIPPED.append((url, "no readable text at that link "
                                      "(a PDF or a page that hides its body behind a script)"))
        return None
    return Document(type=doc_type, content=text, source=url)


def fetch_urls(urls: List[str]) -> List[Document]:
    """Fetch every URL that can be read. `LAST_SKIPPED` explains the rest.

    Silently dropping a link is how a user ends up reading a confident review of
    two documents when they handed in three, so every skip is recorded.
    """
    LAST_SKIPPED.clear()
    out: List[Document] = []
    for u in urls or []:
        d = fetch_url(u)
        if d is not None:
            out.append(d)
    return out


def _html_to_text(html: str) -> str:
    html = _SVG_RE.sub("\n", html)       # drop icon geometry before tags are stripped
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
    text = html.unescape(text)          # &#x27; -> ', &amp; -> & : models read prose
    lines = [_LINE_WS.sub(" ", ln).strip() for ln in text.splitlines()]
    text = "\n".join(lines)
    text = _WS_RE.sub("\n\n", text)
    return _drop_chrome(text)[:50_000]  # cap the text the engine ingests
