#!/usr/bin/env python3
"""
Image Domain Verification Crawler
==================================
Verify that Wix sites with the UserDomainMedia flag serve private images
from the user's custom domain while stock images stay on the global CDN.

Usage:
    python main.py --site https://www.metasiterepublic.com/ --flag-enabled true
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from urllib.parse import urlparse

import httpx

from crawler.config import CrawlConfig
from crawler.domain_validator import validate_foreign_image, validate_image
from crawler.image_extractor import extract_images
from crawler.mock_api import check_user_domain_media_flag, register_mock_site
from crawler.report_generator import build_dataframe, export_csv, print_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("crawler")

FOREIGN_IMAGE_PROBE_ID = "foreign_site_b_image_abc123.jpg"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Image Domain Verification Crawler")
    p.add_argument(
        "--site",
        required=True,
        help="Full URL of the Wix site to crawl (e.g. https://www.metasiterepublic.com/)",
    )
    p.add_argument(
        "--flag-enabled",
        choices=["true", "false"],
        default="true",
        help="Override the UserDomainMedia flag for this run (default: true)",
    )
    p.add_argument(
        "--output",
        default="report.csv",
        help="Path for the CSV report (default: report.csv)",
    )
    p.add_argument(
        "--foreign-image-id",
        default=FOREIGN_IMAGE_PROBE_ID,
        help="Image ID belonging to another site, used for the security probe",
    )
    return p.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    domain = urlparse(args.site).hostname or args.site
    flag_enabled = args.flag_enabled == "true"

    register_mock_site(domain, flag_enabled=flag_enabled)
    meta = await check_user_domain_media_flag(domain)

    if not meta.user_domain_media_enabled:
        log.warning(
            "UserDomainMedia is DISABLED for %s – nothing to validate.", domain
        )
        return 0

    log.info("UserDomainMedia is ENABLED for %s – starting crawl …", domain)

    cfg = CrawlConfig(site_url=args.site, flag_enabled=flag_enabled)

    extraction = await extract_images(args.site)
    if not extraction.images:
        log.warning("No Wix media images found on %s", args.site)
        return 0

    results = []
    async with httpx.AsyncClient(
        headers={"User-Agent": "WixImageCrawler/1.0"},
        follow_redirects=True,
    ) as client:
        for img in extraction.images:
            result = await validate_image(client, img, domain, cfg)
            results.append(result)
            await asyncio.sleep(cfg.backoff)

        log.info("Running foreign-image security probe …")
        sec_result = await validate_foreign_image(
            client, domain, args.foreign_image_id, cfg
        )
        results.append(sec_result)

    df = build_dataframe(results)
    print_summary(df)
    export_csv(df, args.output)

    failures = df[df["Status"].isin(["mismatch", "stock_error", "security_fail", "error"])]
    if not failures.empty:
        log.error("%d issue(s) detected – see report for details", len(failures))
        return 1

    log.info("All checks passed.")
    return 0


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    exit_code = asyncio.run(run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
