"""Tests for the mock flag API."""

from __future__ import annotations

import asyncio

from crawler.mock_api import (
    check_user_domain_media_flag,
    register_mock_site,
)


class TestMockFlagApi:
    def test_registered_site_returns_flag(self):
        register_mock_site("test-enabled.com", flag_enabled=True)

        async def _run():
            return await check_user_domain_media_flag("test-enabled.com")

        meta = asyncio.run(_run())
        assert meta.user_domain_media_enabled is True
        assert meta.domain == "test-enabled.com"

    def test_unregistered_site_defaults_false(self):
        async def _run():
            return await check_user_domain_media_flag("unknown-domain.xyz")

        meta = asyncio.run(_run())
        assert meta.user_domain_media_enabled is False

    def test_toggle_flag(self):
        register_mock_site("toggle.com", flag_enabled=False)

        async def _run():
            m1 = await check_user_domain_media_flag("toggle.com")
            register_mock_site("toggle.com", flag_enabled=True)
            m2 = await check_user_domain_media_flag("toggle.com")
            return m1, m2

        m1, m2 = asyncio.run(_run())
        assert m1.user_domain_media_enabled is False
        assert m2.user_domain_media_enabled is True
