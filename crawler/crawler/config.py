from dataclasses import dataclass, field


STOCK_IMAGE_PREFIXES = ("11062b_", "nsplsh_")

WIXSTATIC_HOST = "static.wixstatic.com"

BACKOFF_SECONDS = 0.5

CACHE_WARM_REQUESTS = 2

HEAD_TIMEOUT_SECONDS = 15.0

FOREIGN_IMAGE_EXPECTED_CODES = (403, 404)


@dataclass
class CrawlConfig:
    site_url: str
    flag_enabled: bool = True
    backoff: float = BACKOFF_SECONDS
    cache_rounds: int = CACHE_WARM_REQUESTS
    timeout: float = HEAD_TIMEOUT_SECONDS
    extra_headers: dict[str, str] = field(default_factory=dict)
