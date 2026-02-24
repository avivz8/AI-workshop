"""
LatencyMonitor – measures TTFB for HEAD requests and computes deltas
between the wixstatic CDN origin and the user-domain proxy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass
class LatencyResult:
    url: str
    ttfb_ms: float
    status_code: int
    headers: dict[str, str]
    cache_hit: bool | None


async def measure_head(
    client: httpx.AsyncClient,
    url: str,
    *,
    timeout: float = 15.0,
) -> LatencyResult:
    """Issue a HEAD request and record TTFB + response metadata."""
    start = time.perf_counter()
    resp = await client.head(url, timeout=timeout, follow_redirects=True)
    ttfb_ms = (time.perf_counter() - start) * 1000

    headers = dict(resp.headers)
    cache_header = (
        headers.get("x-cache", "") or headers.get("cf-cache-status", "")
    ).upper()
    cache_hit: bool | None = None
    if "HIT" in cache_header:
        cache_hit = True
    elif "MISS" in cache_header:
        cache_hit = False

    return LatencyResult(
        url=url,
        ttfb_ms=round(ttfb_ms, 2),
        status_code=resp.status_code,
        headers=headers,
        cache_hit=cache_hit,
    )


def compute_delta(origin: LatencyResult, proxy: LatencyResult) -> float:
    """Return proxy TTFB minus origin TTFB in ms (positive = proxy slower)."""
    return round(proxy.ttfb_ms - origin.ttfb_ms, 2)
