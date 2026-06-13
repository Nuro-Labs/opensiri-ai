"""Permissioned world-knowledge connector."""

from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

from .base import Connector, ConnectorResult


class WebConnector(Connector):
    name = "web"
    source = "web"
    can_read = False
    can_write = False

    def __init__(self, enabled: bool = False):
        self.can_read = enabled

    def execute(self, action_name: str, args: dict) -> ConnectorResult:
        if action_name != "web_search":
            raise ValueError(f"unsupported web action: {action_name}")
        if not self.can_read:
            return ConnectorResult("web access disabled")
        query = str(args.get("query", ""))[:200]
        max_results = max(1, min(int(args.get("max_results", 3) or 3), 5))
        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(url, headers={"User-Agent": "opensiri-ai/0.1"})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(200000).decode("utf-8", errors="replace")
        rows = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
            href = html.unescape(m.group(1))
            title = html.unescape(re.sub(r"<.*?>", "", m.group(2), flags=re.S)).strip()
            rows.append(f"{title} — {href}")
            if len(rows) >= max_results:
                break
        return ConnectorResult("\n".join(rows) if rows else "no web results")
