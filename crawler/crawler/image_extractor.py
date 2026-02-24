"""
ImageExtractor – uses Playwright to load a Wix page headlessly,
then collects every image URL from <img> tags and CSS background-image
properties.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from .config import STOCK_IMAGE_PREFIXES, WIXSTATIC_HOST

log = logging.getLogger(__name__)

_BG_URL_RE = re.compile(r'url\(["\']?(https?://[^"\')\s]+)["\']?\)')


@dataclass
class ImageInfo:
    original_url: str
    filename: str
    transformations: str
    is_stock: bool
    source_type: str  # "img_tag" | "css_background"


@dataclass
class ExtractionResult:
    site_url: str
    images: list[ImageInfo] = field(default_factory=list)


def _parse_wixstatic_url(url: str) -> tuple[str, str] | None:
    """
    Extract (media_id, rest_of_media_path) from a Wix media URL.

    Supports both ``static.wixstatic.com/media/…`` and
    ``{domain}/_media/…`` layouts.  *media_id* is the first path
    segment after the ``/media/`` or ``/_media/`` marker.
    *rest_of_media_path* captures transforms and the display-name
    tail so the proxy URL can be reconstructed faithfully.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path

    if WIXSTATIC_HOST in host:
        marker = "/media/"
    elif "/_media/" in path:
        marker = "/_media/"
    else:
        return None

    idx = path.find(marker)
    if idx == -1:
        return None

    media_path = path[idx + len(marker) :].strip("/")
    if not media_path:
        return None

    parts = media_path.split("/")
    media_id = parts[0]
    rest = "/".join(parts[1:]) if len(parts) > 1 else ""
    return media_id, rest


def _is_stock(filename: str) -> bool:
    return any(filename.startswith(p) for p in STOCK_IMAGE_PREFIXES)


def _build_image_info(url: str, source_type: str) -> ImageInfo | None:
    result = _parse_wixstatic_url(url)
    if result is None:
        return None
    filename, transforms = result
    return ImageInfo(
        original_url=url,
        filename=filename,
        transformations=transforms,
        is_stock=_is_stock(filename),
        source_type=source_type,
    )


async def extract_images(site_url: str) -> ExtractionResult:
    """Launch a headless browser, navigate to *site_url*, and return all
    discovered Wix media image URLs."""
    extraction = ExtractionResult(site_url=site_url)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        log.info("Loading %s …", site_url)
        await page.goto(site_url, wait_until="domcontentloaded", timeout=60_000)
        # Wix SPAs hydrate after DOMContentLoaded; give images time to render
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            log.info("networkidle not reached – continuing with loaded DOM")
        await page.wait_for_timeout(3_000)

        img_srcs: list[str] = await page.eval_on_selector_all(
            "img",
            """els => els.map(e => e.currentSrc || e.src).filter(Boolean)""",
        )
        for src in img_srcs:
            info = _build_image_info(src, "img_tag")
            if info:
                extraction.images.append(info)

        bg_urls: list[str] = await page.evaluate(
            """() => {
                const urls = [];
                for (const el of document.querySelectorAll('*')) {
                    const bg = getComputedStyle(el).backgroundImage;
                    if (bg && bg !== 'none') urls.push(bg);
                }
                return urls;
            }"""
        )
        for raw in bg_urls:
            for match in _BG_URL_RE.finditer(raw):
                info = _build_image_info(match.group(1), "css_background")
                if info:
                    extraction.images.append(info)

        await browser.close()

    log.info("Extracted %d images from %s", len(extraction.images), site_url)
    return extraction
