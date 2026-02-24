from __future__ import annotations

import pytest
import httpx

from crawler.config import CrawlConfig
from crawler.image_extractor import ImageInfo


@pytest.fixture()
def user_domain() -> str:
    return "www.testsite.com"


@pytest.fixture()
def crawl_config(user_domain: str) -> CrawlConfig:
    return CrawlConfig(
        site_url=f"https://{user_domain}/",
        flag_enabled=True,
        backoff=0.0,
        cache_rounds=1,
        timeout=5.0,
    )


@pytest.fixture()
def user_image() -> ImageInfo:
    return ImageInfo(
        original_url="https://static.wixstatic.com/media/abc123_myimage.jpg/v1/fill/w_294,h_577,al_c,q_85,enc_avif/abc123_myimage.jpg",
        filename="abc123_myimage.jpg",
        transformations="v1/fill/w_294,h_577,al_c,q_85,enc_avif",
        is_stock=False,
        source_type="img_tag",
    )


@pytest.fixture()
def stock_image_11062b() -> ImageInfo:
    return ImageInfo(
        original_url="https://static.wixstatic.com/media/11062b_banner.jpg",
        filename="11062b_banner.jpg",
        transformations="",
        is_stock=True,
        source_type="img_tag",
    )


@pytest.fixture()
def stock_image_nsplsh() -> ImageInfo:
    return ImageInfo(
        original_url="https://static.wixstatic.com/media/nsplsh_hero.jpg",
        filename="nsplsh_hero.jpg",
        transformations="",
        is_stock=True,
        source_type="img_tag",
    )
