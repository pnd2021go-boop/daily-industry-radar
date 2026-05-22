from __future__ import annotations

from difflib import SequenceMatcher


def _normalize_url(url: str) -> str:
    return (url or "").split("?utm_")[0].strip().rstrip("/")


def _normalize_title(title: str) -> str:
    return " ".join((title or "").lower().strip().split())


def deduplicate_items(items: list[dict], title_threshold: float = 0.88) -> list[dict]:
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    unique: list[dict] = []

    for item in items:
        url = _normalize_url(item.get("url", ""))
        title = _normalize_title(item.get("title", ""))
        if not title or not url:
            continue
        if url in seen_urls:
            continue
        if any(SequenceMatcher(None, title, old).ratio() >= title_threshold for old in seen_titles):
            continue

        seen_urls.add(url)
        seen_titles.append(title)
        unique.append(item)

    return unique
