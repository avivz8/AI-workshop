"""Unit tests for DomainValidator logic."""

from __future__ import annotations

import pytest

from crawler.domain_validator import build_proxied_url
from crawler.image_extractor import ImageInfo


class TestBuildProxiedUrl:
    def test_user_image_without_transforms(self):
        img = ImageInfo(
            original_url="https://static.wixstatic.com/media/abc123_photo.jpg",
            filename="abc123_photo.jpg",
            transformations="",
            is_stock=False,
            source_type="img_tag",
        )
        url = build_proxied_url(img, "www.mysite.com")
        assert url == "https://www.mysite.com/_media/abc123_photo.jpg"

    def test_user_image_with_transforms(self):
        img = ImageInfo(
            original_url="https://static.wixstatic.com/media/abc123_photo.jpg/v1/fill/w_294,h_577/abc123_photo.jpg",
            filename="abc123_photo.jpg",
            transformations="v1/fill/w_294,h_577/abc123_photo.jpg",
            is_stock=False,
            source_type="img_tag",
        )
        url = build_proxied_url(img, "www.mysite.com")
        assert url == "https://www.mysite.com/_media/abc123_photo.jpg/v1/fill/w_294,h_577/abc123_photo.jpg"

    def test_stock_image_returns_none(self):
        img = ImageInfo(
            original_url="https://static.wixstatic.com/media/11062b_banner.jpg",
            filename="11062b_banner.jpg",
            transformations="",
            is_stock=True,
            source_type="img_tag",
        )
        assert build_proxied_url(img, "www.mysite.com") is None

    def test_nsplsh_stock_returns_none(self):
        img = ImageInfo(
            original_url="https://static.wixstatic.com/media/nsplsh_hero.jpg",
            filename="nsplsh_hero.jpg",
            transformations="",
            is_stock=True,
            source_type="img_tag",
        )
        assert build_proxied_url(img, "www.mysite.com") is None
