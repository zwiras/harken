"""DuckDuckGo HTML SERP source for Harken — no API key."""

from __future__ import annotations

import re
import time
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse

from harken.models import Mention, utcnow
from harken.sources.base import Source, strip_html

_RESULT_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
_SNIPPET_RE = re.compile(
    r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|td|div|span)',
    re.I | re.S,
)

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _unwrap_ddg(href: str) -> str:
    if "uddg=" in href:
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    if href.startswith("//"):
        return "https:" + href
    return href


class SerpSource(Source):
    """Search-engine mentions via DuckDuckGo HTML (fragile, free, no key)."""

    name = "serp"
    label = "Serp"
    needs_config = False

    def __init__(self, delay_sec: float = 2.5, **options):
        super().__init__(**options)
        self.delay_sec = delay_sec

    def fetch(self, query: str, limit: int = 50) -> list[Mention]:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": _BROWSER_UA,
            "Accept": "text/html",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
        with self._client(headers=headers) as client:
            resp = client.get(url, params={"q": query})
            resp.raise_for_status()
            html = resp.text

        snippets = [strip_html(m.group(1)) for m in _SNIPPET_RE.finditer(html)]
        mentions: list[Mention] = []
        now = utcnow()
        for i, m in enumerate(_RESULT_RE.finditer(html)):
            link = _unwrap_ddg(unescape(m.group(1)))
            title = strip_html(m.group(2))
            if not link.startswith("http"):
                continue
            snippet = snippets[i] if i < len(snippets) else ""
            mentions.append(
                Mention(
                    source=self.name,
                    query=query,
                    author=None,
                    title=title or None,
                    text=snippet,
                    url=link,
                    created_at=now,
                )
            )
            if len(mentions) >= limit:
                break

        time.sleep(self.delay_sec)
        return mentions
