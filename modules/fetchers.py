from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import logging
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

import feedparser
import requests
from googlenewsdecoder import gnewsdecoder


USER_AGENT = "DailyIndustryRadar/1.0 (+https://github.com/)"
logger = logging.getLogger("daily-industry-radar.fetchers")

PUBLISHER_BY_DOMAIN = {
    "reuters.com": "Reuters", "bloomberg.com": "Bloomberg", "wsj.com": "The Wall Street Journal",
    "cnbc.com": "CNBC", "techcrunch.com": "TechCrunch", "theverge.com": "The Verge",
    "wired.com": "Wired", "axios.com": "Axios", "fortune.com": "Fortune",
    "businessinsider.com": "Business Insider", "retaildive.com": "Retail Dive",
    "modernretail.co": "Modern Retail", "businessofhome.com": "Business of Home",
    "furnituretoday.com": "Furniture Today", "homenewsnow.com": "Home News Now",
    "digitalcommerce360.com": "Digital Commerce 360", "supplychaindive.com": "Supply Chain Dive",
    "shopify.com": "Shopify", "aboutamazon.com": "Amazon", "openai.com": "OpenAI",
    "anthropic.com": "Anthropic", "blog.google": "Google", "microsoft.com": "Microsoft",
}


def _parse_datetime(entry: Any) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                parsed = parsedate_to_datetime(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def _original_url(url: str, discovery_source: str) -> str:
    if discovery_source.startswith("Bing News:") and "bing.com/news/apiclick" in url:
        direct = parse_qs(urlparse(url).query).get("url", [""])[0]
        return direct or url
    return url


def resolve_original_url(item: dict) -> dict:
    url = item.get("url", "")
    if "news.google.com/" not in url:
        return item
    try:
        result = gnewsdecoder(url)
        decoded = result.get("decoded_url", "") if result.get("status") else ""
        if decoded:
            item["url"] = decoded
    except Exception as exc:
        logger.info("Could not decode Google News URL for %s: %s", item.get("title", ""), exc)
    return item


def _publisher_for_url(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    for domain, publisher in PUBLISHER_BY_DOMAIN.items():
        if host == domain or host.endswith(f".{domain}"):
            return publisher
    return host


def _entry_publisher(entry: Any, discovery_source: str, url: str) -> str:
    source = entry.get("source") or {}
    publisher = ""
    if isinstance(source, dict):
        publisher = (source.get("title") or "").strip()
    else:
        publisher = (getattr(source, "title", "") or "").strip()

    title = (entry.get("title") or "").strip()
    if not publisher and discovery_source.startswith("Google News:") and " - " in title:
        publisher = title.rsplit(" - ", 1)[-1].strip()
    if not publisher and discovery_source.startswith("Bing News:"):
        publisher = _publisher_for_url(url)
    return publisher or discovery_source


def _clean_google_news_title(title: str, publisher: str, discovery_source: str) -> str:
    if not discovery_source.startswith("Google News:") or not publisher:
        return title
    suffix = f" - {publisher}"
    return title[:-len(suffix)].strip() if title.endswith(suffix) else title


def _entry_to_item(entry: Any, source_name: str, category: str | None) -> dict:
    published_at = _parse_datetime(entry)
    raw_title = (entry.get("title") or "").strip()
    url = _original_url((entry.get("link") or "").strip(), source_name)
    publisher = _entry_publisher(entry, source_name, url)
    return {
        "title": _clean_google_news_title(raw_title, publisher, source_name),
        "summary_raw": (entry.get("summary") or entry.get("description") or "").strip(),
        "source_name": publisher,
        "discovery_source": source_name,
        "published_at": published_at.isoformat() if published_at else "",
        "url": url,
        "category_hint": category,
    }


def _is_recent(item: dict, since: datetime) -> bool:
    value = item.get("published_at")
    if not value:
        return True
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc) >= since
    except ValueError:
        return True


def fetch_rss_sources(sources: list[dict], lookback_hours: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    items: list[dict] = []
    for source in sources:
        name = source.get("name", "RSS")
        url = source.get("url")
        if not url:
            continue
        try:
            parsed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
        except Exception as exc:
            logger.warning("Skipping RSS source %s after parse failure: %s", name, exc)
            continue
        if getattr(parsed, "bozo", False):
            logger.warning(
                "RSS source %s reported parse warning: %s",
                name,
                getattr(parsed, "bozo_exception", "unknown"),
            )
        for entry in parsed.entries:
            item = _entry_to_item(entry, name, source.get("category"))
            if _is_recent(item, since):
                items.append(item)
    return items


def build_google_news_url(keyword: str, language: str = "en-US", region: str = "US") -> str:
    query = quote_plus(f'{keyword} when:2d')
    return f"https://news.google.com/rss/search?q={query}&hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"


def build_bing_news_url(keyword: str, language: str = "en-US") -> str:
    query = quote_plus(keyword)
    return f"https://www.bing.com/news/search?q={query}&format=rss&setlang={language.lower()}"


def fetch_google_news(keyword_config: dict, language: str, region: str, lookback_hours: int) -> list[dict]:
    sources = []
    for category, keywords in keyword_config.items():
        for keyword in keywords:
            sources.append({
                "name": f"Google News: {keyword}",
                "url": build_google_news_url(keyword, language, region),
                "category": category,
            })
    return fetch_rss_sources(sources, lookback_hours)


def fetch_bing_news(keyword_config: dict, language: str, lookback_hours: int) -> list[dict]:
    sources = []
    for category, keywords in keyword_config.items():
        for keyword in keywords:
            sources.append({
                "name": f"Bing News: {keyword}",
                "url": build_bing_news_url(keyword, language),
                "category": category,
            })
    return fetch_rss_sources(sources, lookback_hours)


def fetch_all(config: dict) -> list[dict]:
    site = config.get("site", {})
    lookback_hours = int(site.get("lookback_hours", 48))
    rss_items = fetch_rss_sources(config.get("rss_sources", []), lookback_hours)

    google_config = config.get("google_news", {})
    bing_config = config.get("bing_news", {})
    keyword_config = google_config.get("keywords", {})
    bing_items = fetch_bing_news(
        keyword_config,
        bing_config.get("language", google_config.get("language", "en-US")),
        lookback_hours,
    ) if bing_config.get("enabled", True) else []
    google_items = fetch_google_news(
        keyword_config,
        google_config.get("language", "en-US"),
        google_config.get("region", "US"),
        lookback_hours,
    )
    return rss_items + bing_items + google_items


def check_url_reachable(url: str, timeout: int = 10) -> bool:
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": USER_AGENT})
        return response.status_code < 400
    except requests.RequestException:
        return False
