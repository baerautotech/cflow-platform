from __future__ import annotations

from typing import Any, Dict, List
import re
from urllib.parse import urlencode

import httpx


class InternetSearchHandlers:
    """Handlers for internet search operations using DuckDuckGo HTML endpoints.

    Enforces a strict allowlist to only query DuckDuckGo HTML search endpoints.
    Extracts titles, URLs, and snippets from the results page and returns
    a concise summary along with sources.
    """

    _ALLOWED_HOSTS: List[str] = [
        "duckduckgo.com",
        "html.duckduckgo.com",
    ]

    _SEARCH_BASES: List[str] = [
        "https://html.duckduckgo.com/html/",
        "https://duckduckgo.com/html/",
    ]

    async def handle_internet_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        query: str = (arguments.get("query") or "").strip()
        if not query:
            return {"status": "error", "message": "query is required"}

        max_results_raw = arguments.get("max_results") or arguments.get("limit") or 5
        try:
            max_results = max(1, min(int(max_results_raw), 10))
        except Exception:
            max_results = 5

        region: str | None = (arguments.get("region") or None)
        safe: bool = bool(arguments.get("safe", True))

        params: Dict[str, Any] = {"q": query}
        if safe:
            params["kp"] = "1"
        if region:
            params["kl"] = region

        result_items: List[Dict[str, str]] = []

        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=5.0)) as client:
            content: str | None = None
            for base in self._SEARCH_BASES:
                try:
                    url = f"{base}?{urlencode(params)}"
                    if not self._is_url_allowed(url):
                        continue
                    resp = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    })
                    if resp.status_code == 200 and resp.text:
                        content = resp.text
                        break
                except Exception:
                    continue

        if not content:
            return {"status": "error", "message": "search unavailable"}

        result_items = self._extract_results(content)[:max_results]

        summary = self._summarize(result_items, query)

        return {
            "status": "success",
            "query": query,
            "summary": summary,
            "sources": result_items,
            "metadata": {
                "provider": "duckduckgo",
                "result_count": len(result_items),
                "safe": safe,
                "region": region,
            },
        }

    def _is_url_allowed(self, url: str) -> bool:
        m = re.match(r"^https?://([^/]+)(/|$)", url)
        if not m:
            return False
        host = m.group(1).lower()
        return any(host == h or host.endswith("." + h) for h in self._ALLOWED_HOSTS)

    def _extract_results(self, html: str) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        # Basic parsing for DuckDuckGo HTML: anchors with class result__a and snippets with class result__snippet
        # Title and URL
        anchor_pattern = re.compile(r"<a[^>]*class=\"result__a[^\"]*\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
        # Snippet
        snippet_pattern = re.compile(r"<a[^>]*class=\"result__a[^\"]*\"[^>]*>.*?</a>.*?<a[^>]*class=\"result__snippet[^\"]*\"[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)

        anchors = list(anchor_pattern.finditer(html))
        snippets = list(snippet_pattern.finditer(html))

        snippet_texts: List[str] = []
        for s in snippets:
            snippet_html = s.group(1)
            snippet_texts.append(self._strip_html(snippet_html))

        for idx, a in enumerate(anchors):
            href = self._strip_tracking(a.group(1))
            title_html = a.group(2)
            title = self._strip_html(title_html)
            snippet = snippet_texts[idx] if idx < len(snippet_texts) else ""
            if href and title:
                items.append({"title": title[:200], "url": href, "snippet": snippet[:500]})

        # Fallback: try another snippet selector variation if none found
        if not items:
            alt_anchor = re.compile(r"<a[^>]*class=\"result__a[^\"]*\"[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
            for a in alt_anchor.finditer(html):
                href = self._strip_tracking(a.group(1))
                title = self._strip_html(a.group(2))
                if href and title:
                    items.append({"title": title[:200], "url": href, "snippet": ""})

        return items

    def _strip_html(self, text: str) -> str:
        # Remove tags and decode basic entities
        no_tags = re.sub(r"<[^>]+>", " ", text)
        no_tags = re.sub(r"&nbsp;", " ", no_tags)
        no_tags = re.sub(r"&amp;", "&", no_tags)
        no_tags = re.sub(r"&lt;", "<", no_tags)
        no_tags = re.sub(r"&gt;", ">", no_tags)
        # Collapse whitespace
        return re.sub(r"\s+", " ", no_tags).strip()

    def _strip_tracking(self, url: str) -> str:
        # DuckDuckGo HTML may include external tracking redirect; prefer direct URLs when present
        m = re.search(r"uddg=([^&]+)", url)
        if m:
            try:
                from urllib.parse import unquote

                return unquote(m.group(1))
            except Exception:
                return url
        return url

    def _summarize(self, items: List[Dict[str, str]], query: str) -> str:
        if not items:
            return "No results found."
        fragments: List[str] = []
        for it in items:
            title = it.get("title", "").strip()
            snippet = it.get("snippet", "").strip()
            if title and snippet:
                fragments.append(f"- {title}: {snippet}")
            elif title:
                fragments.append(f"- {title}")
        joined = "\n".join(fragments)
        if len(joined) > 1200:
            joined = joined[:1197] + "..."
        return joined


