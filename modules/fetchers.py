from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import logging
from typing import Any
from urllib.parse import quote_plus

import feedparser
import requests


USER_AGENT = "DailyIndustryRadar/1.0 (+https://github.com/)"
logger = logging.getLogger("daily-industry-radar.fetchers")


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


def _entry_to_item(entry: Any, source_name: str, category: str | None) -> dict:
    published_at = _parse_datetime(entry)
    return {
        "title": (entry.get("title") or "").strip(),
        "summary_raw": (entry.get("summary") or entry.get("description") or "").strip(),
        "source_name": source_name,
        "published_at": published_at.isoformat() if published_at else "",
        "url": (entry.get("link") or "").strip(),
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


def fetch_all(config: dict) -> list[dict]:
    site = config.get("site", {})
    lookback_hours = int(site.get("lookback_hours", 48))
    rss_items = fetch_rss_sources(config.get("rss_sources", []), lookback_hours)

    google_config = config.get("google_news", {})
    google_items = fetch_google_news(
        google_config.get("keywords", {}),
        google_config.get("language", "en-US"),
        google_config.get("region", "US"),
        lookback_hours,
    )
    return rss_items + google_items


def check_url_reachable(url: str, timeout: int = 10) -> bool:
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": USER_AGENT})
        return response.status_code < 400
    except requests.RequestException:
        return False
