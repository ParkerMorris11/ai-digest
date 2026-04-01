"""Newsletter fetchers for The Rundown AI, TLDR AI, Superhuman AI, and The Neuron.

All requests use a shared SSL context built from the certifi certificate bundle,
which resolves the SSL certificate verification errors common on macOS.
"""

import logging
import re
import ssl
import certifi
from datetime import date
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)

# Shared SSL context — uses certifi's CA bundle to fix macOS cert issues.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36"
    )
}


class _HTMLTextExtractor(HTMLParser):
    """Strips HTML tags and returns plain text, skipping script/style blocks."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "li"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts).strip()


def _html_to_text(html: str) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


def _fetch_raw(url: str, timeout: int = 30) -> str:
    """Return raw HTML from *url*, or an empty string on failure."""
    req = Request(url, headers=_HEADERS)
    try:
        with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return ""


def _fetch_text(url: str, timeout: int = 30) -> str:
    """Return plain text extracted from *url*, or an empty string on failure."""
    html = _fetch_raw(url, timeout)
    return _html_to_text(html) if html else ""


def fetch_rundown_ai() -> str:
    """Fetch the latest issue of The Rundown AI."""
    logger.info("Fetching The Rundown AI...")
    archive_html = _fetch_raw("https://www.therundown.ai/archive")
    if archive_html:
        links = re.findall(
            r'href="(https://www\.therundown\.ai/p/[^"]+)"', archive_html
        )
        if links:
            logger.info("  Found issue: %s", links[0])
            return _fetch_text(links[0])
    return _fetch_text("https://www.therundown.ai/archive")


def fetch_tldr_ai() -> str:
    """Fetch today's TLDR AI issue, falling back to the homepage."""
    logger.info("Fetching TLDR AI...")
    today = date.today().strftime("%Y-%m-%d")
    content = _fetch_text(f"https://tldr.tech/ai/{today}")
    if not content or len(content) < 200:
        content = _fetch_text("https://tldr.tech/ai")
    return content


def fetch_superhuman_ai() -> str:
    """Fetch the latest issue of Superhuman AI."""
    logger.info("Fetching Superhuman AI...")
    homepage_html = _fetch_raw("https://www.superhuman.ai")
    if homepage_html:
        links = re.findall(
            r'href="(https://www\.superhuman\.ai/p/[^"]+)"', homepage_html
        )
        if links:
            logger.info("  Found issue: %s", links[0])
            return _fetch_text(links[0])
    return _fetch_text("https://www.superhuman.ai")


def fetch_neuron_ai() -> str:
    """Fetch the latest issue of The Neuron."""
    logger.info("Fetching The Neuron...")
    archive_html = _fetch_raw("https://www.theneurondaily.com/archive")
    if archive_html:
        # Links may be absolute or relative paths.
        slugs = re.findall(r'href="(/p/[^"]+)"', archive_html)
        absolute = re.findall(
            r'href="(https://www\.theneurondaily\.com/p/[^"]+)"', archive_html
        )
        if absolute:
            url = absolute[0]
        elif slugs:
            url = f"https://www.theneurondaily.com{slugs[0]}"
        else:
            url = None
        if url:
            logger.info("  Found issue: %s", url)
            return _fetch_text(url)
    return _fetch_text("https://www.theneurondaily.com")
