"""
ReportGenerator – turns a list of ValidationResults into a pandas
DataFrame and exports it to CSV / prints a summary table.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .domain_validator import ValidationResult

log = logging.getLogger(__name__)


def _row(r: ValidationResult) -> dict:
    cache_hit_str = ""
    if r.cache_results:
        hits = [cr.cache_hit for cr in r.cache_results if cr.cache_hit is not None]
        if hits:
            cache_hit_str = "Hit" if any(hits) else "Miss"

    return {
        "Original URL": r.original_url or "(security probe)",
        "Proxied URL": r.proxied_url or "",
        "Status": r.status,
        "Detail": r.detail,
        "Latency Delta (ms)": r.latency_delta_ms if r.latency_delta_ms is not None else "",
        "Is Stock?": r.image.is_stock,
        "Origin TTFB (ms)": r.original_head.ttfb_ms if r.original_head else "",
        "Proxy TTFB (ms)": r.proxied_head.ttfb_ms if r.proxied_head else "",
        "Cache (2nd req)": cache_hit_str,
    }


def build_dataframe(results: list[ValidationResult]) -> pd.DataFrame:
    rows = [_row(r) for r in results]
    return pd.DataFrame(rows)


def export_csv(df: pd.DataFrame, path: str | Path = "report.csv") -> Path:
    out = Path(path)
    df.to_csv(out, index=False)
    log.info("Report written to %s (%d rows)", out.resolve(), len(df))
    return out


def print_summary(df: pd.DataFrame) -> None:
    counts = df["Status"].value_counts()
    total = len(df)
    print("\n===== Crawl Summary =====")
    print(f"Total images checked: {total}")
    for status, count in counts.items():
        print(f"  {status}: {count}")
    print("=========================\n")
    print(df.to_string(index=False))
