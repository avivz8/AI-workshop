"""Security probe tests – foreign image access must be rejected."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from crawler.config import CrawlConfig, FOREIGN_IMAGE_EXPECTED_CODES
from crawler.domain_validator import validate_foreign_image


class TestForeignImageSecurity:
    @pytest.mark.parametrize("code", FOREIGN_IMAGE_EXPECTED_CODES)
    def test_expected_reject_codes_pass(self, code: int):
        """Verify that 403 and 404 both count as security_pass."""
        transport = httpx.MockTransport(
            lambda req: httpx.Response(code, headers={"server": "mock"})
        )
        cfg = CrawlConfig(site_url="https://site-a.com/", backoff=0)

        async def _run():
            async with httpx.AsyncClient(transport=transport) as client:
                return await validate_foreign_image(
                    client, "site-a.com", "site_b_image.jpg", cfg
                )

        result = asyncio.run(_run())
        assert result.status == "security_pass"

    def test_200_is_security_fail(self):
        """If the server returns 200, the foreign image leaked."""
        transport = httpx.MockTransport(
            lambda req: httpx.Response(200, headers={"server": "mock"})
        )
        cfg = CrawlConfig(site_url="https://site-a.com/", backoff=0)

        async def _run():
            async with httpx.AsyncClient(transport=transport) as client:
                return await validate_foreign_image(
                    client, "site-a.com", "site_b_image.jpg", cfg
                )

        result = asyncio.run(_run())
        assert result.status == "security_fail"
