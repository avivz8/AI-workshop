"""Unit tests for image_extractor helpers (no browser needed)."""

from __future__ import annotations

from crawler.image_extractor import _build_image_info, _is_stock, _parse_wixstatic_url


class TestParseWixstaticUrl:
    def test_standard_media_url(self):
        url = "https://static.wixstatic.com/media/abc123_img.jpg"
        result = _parse_wixstatic_url(url)
        assert result is not None
        filename, transforms = result
        assert filename == "abc123_img.jpg"

    def test_url_with_transformations(self):
        url = "https://static.wixstatic.com/media/abc123_img.jpg/v1/fill/w_294,h_577,al_c,q_85,enc_avif/abc123_img.jpg"
        result = _parse_wixstatic_url(url)
        assert result is not None
        media_id, rest = result
        assert media_id == "abc123_img.jpg"
        assert "w_294" in rest

    def test_non_wix_url_returns_none(self):
        assert _parse_wixstatic_url("https://cdn.example.com/photo.png") is None

    def test_media_path_on_user_domain(self):
        url = "https://www.mysite.com/_media/abc123_img.jpg"
        result = _parse_wixstatic_url(url)
        assert result is not None
        assert result[0] == "abc123_img.jpg"


class TestIsStock:
    def test_11062b_prefix(self):
        assert _is_stock("11062b_banner.jpg") is True

    def test_nsplsh_prefix(self):
        assert _is_stock("nsplsh_hero.webp") is True

    def test_user_image(self):
        assert _is_stock("abc123_photo.jpg") is False


class TestBuildImageInfo:
    def test_returns_image_info_for_valid_url(self):
        url = "https://static.wixstatic.com/media/abc123_img.jpg"
        info = _build_image_info(url, "img_tag")
        assert info is not None
        assert info.filename == "abc123_img.jpg"
        assert info.is_stock is False
        assert info.source_type == "img_tag"

    def test_stock_image_flagged(self):
        url = "https://static.wixstatic.com/media/11062b_stock.jpg"
        info = _build_image_info(url, "css_background")
        assert info is not None
        assert info.is_stock is True

    def test_non_wix_url_returns_none(self):
        assert _build_image_info("https://other.cdn/img.png", "img_tag") is None
