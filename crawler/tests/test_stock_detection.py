"""Tests ensuring stock images are correctly identified and never proxied."""

from __future__ import annotations

import pytest

from crawler.config import STOCK_IMAGE_PREFIXES
from crawler.domain_validator import build_proxied_url, validate_image
from crawler.image_extractor import ImageInfo


class TestStockDetection:
    @pytest.mark.parametrize("prefix", STOCK_IMAGE_PREFIXES)
    def test_stock_prefix_detected(self, prefix: str):
        img = ImageInfo(
            original_url=f"https://static.wixstatic.com/media/{prefix}img.jpg",
            filename=f"{prefix}img.jpg",
            transformations="",
            is_stock=True,
            source_type="img_tag",
        )
        assert img.is_stock is True
        assert build_proxied_url(img, "site.com") is None

    def test_stock_on_user_domain_is_flagged(self):
        """If a stock image somehow shows up on a user domain, validation
        should flag it as ``stock_error``."""
        img = ImageInfo(
            original_url="https://www.mysite.com/_media/11062b_banner.jpg",
            filename="11062b_banner.jpg",
            transformations="",
            is_stock=True,
            source_type="img_tag",
        )
        from crawler.config import CrawlConfig

        cfg = CrawlConfig(site_url="https://www.mysite.com/", backoff=0)
        import asyncio, httpx

        async def _run():
            async with httpx.AsyncClient() as client:
                return await validate_image(client, img, "www.mysite.com", cfg)

        result = asyncio.run(_run())
        assert result.status == "stock_error"
