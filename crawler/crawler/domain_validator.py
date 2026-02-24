"""
DomainValidator – for each extracted image, performs HEAD requests against
both the original wixstatic URL and the proxied user-domain URL.  Compares
status codes, selected headers, and latency via LatencyMonitor.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from .config import (
    FOREIGN_IMAGE_EXPECTED_CODES,
    STOCK_IMAGE_PREFIXES,
    WIXSTATIC_HOST,
    CrawlConfig,
)
from .image_extractor import ImageInfo
from .latency_monitor import LatencyResult, compute_delta, measure_head

log = logging.getLogger(__name__)

COMPARED_HEADERS = ("x-seen-by", "cache-control", "server")


@dataclass
class ValidationResult:
    image: ImageInfo
    original_url: str
    proxied_url: str | None
    original_head: LatencyResult | None
    proxied_head: LatencyResult | None
    latency_delta_ms: float | None
    status: str  # "match" | "mismatch" | "stock_ok" | "stock_error" | "security_pass" | "security_fail" | "error"
    detail: str = ""
    cache_results: list[LatencyResult] | None = None


def build_proxied_url(image: ImageInfo, user_domain: str) -> str | None:
    """Construct the ``https://{user_domain}/_media/{media_id}/{rest}`` URL.
    Returns None for stock images (they must stay on the CDN)."""
    if image.is_stock:
        return None
    path = f"/_media/{image.filename}"
    if image.transformations:
        path = f"/_media/{image.filename}/{image.transformations}"
    return f"https://{user_domain}{path}"


def _header_match(a: dict[str, str], b: dict[str, str]) -> tuple[bool, str]:
    mismatches: list[str] = []
    for h in COMPARED_HEADERS:
        va = a.get(h, "")
        vb = b.get(h, "")
        if va != vb:
            mismatches.append(f"{h}: '{va}' vs '{vb}'")
    if mismatches:
        return False, "; ".join(mismatches)
    return True, ""


async def validate_image(
    client: httpx.AsyncClient,
    image: ImageInfo,
    user_domain: str,
    cfg: CrawlConfig,
) -> ValidationResult:
    """Run the full validation sequence for a single image."""
    proxied_url = build_proxied_url(image, user_domain)

    if image.is_stock:
        parsed = urlparse(image.original_url)
        if parsed.hostname and WIXSTATIC_HOST not in parsed.hostname:
            return ValidationResult(
                image=image,
                original_url=image.original_url,
                proxied_url=None,
                original_head=None,
                proxied_head=None,
                latency_delta_ms=None,
                status="stock_error",
                detail="Stock image served from user domain instead of CDN",
            )
        return ValidationResult(
            image=image,
            original_url=image.original_url,
            proxied_url=None,
            original_head=None,
            proxied_head=None,
            latency_delta_ms=None,
            status="stock_ok",
            detail="Stock image correctly on CDN",
        )

    if proxied_url is None:
        return ValidationResult(
            image=image,
            original_url=image.original_url,
            proxied_url=None,
            original_head=None,
            proxied_head=None,
            latency_delta_ms=None,
            status="error",
            detail="Could not build proxied URL",
        )

    try:
        orig_head = await measure_head(client, image.original_url, timeout=cfg.timeout)
        await asyncio.sleep(cfg.backoff)
        proxy_head = await measure_head(client, proxied_url, timeout=cfg.timeout)

        cache_results: list[LatencyResult] = []
        for _ in range(cfg.cache_rounds - 1):
            await asyncio.sleep(cfg.backoff)
            cache_results.append(
                await measure_head(client, proxied_url, timeout=cfg.timeout)
            )

        delta = compute_delta(orig_head, proxy_head)

        ok, mismatch_detail = _header_match(orig_head.headers, proxy_head.headers)
        if orig_head.status_code != proxy_head.status_code:
            status = "mismatch"
            detail = f"Status {orig_head.status_code} vs {proxy_head.status_code}"
        elif not ok:
            status = "mismatch"
            detail = mismatch_detail
        else:
            status = "match"
            detail = ""

        return ValidationResult(
            image=image,
            original_url=image.original_url,
            proxied_url=proxied_url,
            original_head=orig_head,
            proxied_head=proxy_head,
            latency_delta_ms=delta,
            status=status,
            detail=detail,
            cache_results=cache_results,
        )

    except httpx.HTTPError as exc:
        return ValidationResult(
            image=image,
            original_url=image.original_url,
            proxied_url=proxied_url,
            original_head=None,
            proxied_head=None,
            latency_delta_ms=None,
            status="error",
            detail=str(exc),
        )


async def validate_foreign_image(
    client: httpx.AsyncClient,
    site_a_domain: str,
    foreign_image_id: str,
    cfg: CrawlConfig,
) -> ValidationResult:
    """
    Security test: try to reach a foreign image (belonging to site B)
    through site A's /_media/ proxy.  Expects 403 or 404.
    """
    url = f"https://{site_a_domain}/_media/{foreign_image_id}"
    dummy_image = ImageInfo(
        original_url="",
        filename=foreign_image_id,
        transformations="",
        is_stock=False,
        source_type="security_probe",
    )

    try:
        head = await measure_head(client, url, timeout=cfg.timeout)
        if head.status_code in FOREIGN_IMAGE_EXPECTED_CODES:
            return ValidationResult(
                image=dummy_image,
                original_url="",
                proxied_url=url,
                original_head=None,
                proxied_head=head,
                latency_delta_ms=None,
                status="security_pass",
                detail=f"Got expected {head.status_code}",
            )
        return ValidationResult(
            image=dummy_image,
            original_url="",
            proxied_url=url,
            original_head=None,
            proxied_head=head,
            latency_delta_ms=None,
            status="security_fail",
            detail=f"Expected 403/404, got {head.status_code}",
        )
    except httpx.HTTPError as exc:
        return ValidationResult(
            image=dummy_image,
            original_url="",
            proxied_url=url,
            original_head=None,
            proxied_head=None,
            latency_delta_ms=None,
            status="error",
            detail=str(exc),
        )
