"""Tests for the report generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from crawler.domain_validator import ValidationResult
from crawler.image_extractor import ImageInfo
from crawler.latency_monitor import LatencyResult
from crawler.report_generator import build_dataframe, export_csv


def _make_result(status: str = "match") -> ValidationResult:
    return ValidationResult(
        image=ImageInfo(
            original_url="https://static.wixstatic.com/media/abc_img.jpg",
            filename="abc_img.jpg",
            transformations="",
            is_stock=False,
            source_type="img_tag",
        ),
        original_url="https://static.wixstatic.com/media/abc_img.jpg",
        proxied_url="https://www.test.com/_media/abc_img.jpg",
        original_head=LatencyResult(
            url="https://static.wixstatic.com/media/abc_img.jpg",
            ttfb_ms=45.0,
            status_code=200,
            headers={},
            cache_hit=None,
        ),
        proxied_head=LatencyResult(
            url="https://www.test.com/_media/abc_img.jpg",
            ttfb_ms=150.0,
            status_code=200,
            headers={},
            cache_hit=True,
        ),
        latency_delta_ms=105.0,
        status=status,
    )


class TestReportGenerator:
    def test_build_dataframe_columns(self):
        df = build_dataframe([_make_result()])
        expected_cols = {
            "Original URL",
            "Proxied URL",
            "Status",
            "Detail",
            "Latency Delta (ms)",
            "Is Stock?",
            "Origin TTFB (ms)",
            "Proxy TTFB (ms)",
            "Cache (2nd req)",
        }
        assert set(df.columns) == expected_cols

    def test_build_dataframe_row_count(self):
        df = build_dataframe([_make_result(), _make_result("mismatch")])
        assert len(df) == 2

    def test_export_csv_creates_file(self):
        df = build_dataframe([_make_result()])
        with tempfile.TemporaryDirectory() as tmp:
            path = export_csv(df, Path(tmp) / "out.csv")
            assert path.exists()
            contents = path.read_text()
            assert "Original URL" in contents
