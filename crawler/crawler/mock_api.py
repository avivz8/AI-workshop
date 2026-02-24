"""
Mock API layer for the MSM-Writer / UserDomainMedia flag.

Replace the bodies of these functions with real HTTP calls once
production endpoints are available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

_FLAG_REGISTRY: dict[str, bool] = {
    "www.metasiterepublic.com": True,
    "example-disabled.com": False,
}


@dataclass
class SiteMetadata:
    domain: str
    user_domain_media_enabled: bool
    meta_site_id: str


async def check_user_domain_media_flag(domain: str) -> SiteMetadata:
    """Return mocked site metadata including the UserDomainMedia flag."""
    enabled = _FLAG_REGISTRY.get(domain, False)
    log.info("Flag check for %s → UserDomainMedia=%s (mocked)", domain, enabled)
    return SiteMetadata(
        domain=domain,
        user_domain_media_enabled=enabled,
        meta_site_id=f"mock-msid-{domain.replace('.', '-')}",
    )


def register_mock_site(domain: str, *, flag_enabled: bool) -> None:
    """Allow tests / CLI to inject flag state at runtime."""
    _FLAG_REGISTRY[domain] = flag_enabled
