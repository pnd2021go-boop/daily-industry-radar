from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from dotenv import load_dotenv

from modules.archive import append_news_archive, write_markdown_backup
from modules.classifier import classify_item
from modules.deduplicator import deduplicate_items
from modules.fetchers import fetch_all
from modules.render_pages import write_pages
from modules.summarizer import has_enough_source_text, summarize_item


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("daily-industry-radar")


CATEGORY_ORDER = [
    "cross_border_ecommerce",
    "furniture_home",
    "ai_tech",
    "consumer_retail",
    "others",
]


def load_config(path: Path = Path("config.yaml")) -> dict:
    if not path.exists():
        raise FileNotFoundError("config.yaml not found")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def report_date(config: dict) -> str:
    timezone_name = config.get("site", {}).get("timezone", "Asia/Shanghai")
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning("Timezone %s not found; falling back to UTC+8", timezone_name)
        tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d")


def enrich_items(items: list[dict], max_items: int) -> list[dict]:
    classified: list[dict] = []
    for item in items:
        classification = classify_item(
            item.get("title", ""),
            item.get("summary_raw", ""),
            item.get("category_hint"),
        )
        item["category"] = classification.category
        item["importance_score"] = classification.importance_score
        classified.append(item)

    for category in CATEGORY_ORDER:
        logger.info(
            "Classified %s items as %s",
            sum(1 for item in classified if item.get("category") == category),
            category,
        )

    def sort_key(item: dict) -> tuple[int, str]:
        return int(item.get("importance_score", 1)), item.get("published_at", "")

    groups: dict[str, list[dict]] = {category: [] for category in CATEGORY_ORDER}
    for item in classified:
        groups.setdefault(item.get("category", "others"), []).append(item)

    for grouped_items in groups.values():
        grouped_items.sort(key=sort_key, reverse=True)

    selected: list[dict] = []
    selected_urls: set[str] = set()

    def try_select(item: dict) -> bool:
        url = item.get("url", "")
        if url in selected_urls:
            return False
        if not has_enough_source_text(item):
            logger.info("Skipping item with insufficient source text: %s", item.get("title", ""))
            return False
        selected.append(summarize_item(item))
        if url:
            selected_urls.add(url)
        return True

    per_category_quota = max(2, max_items // max(1, len(CATEGORY_ORDER)))
    per_category_scan_limit = max(25, max_items)
    for category in CATEGORY_ORDER:
        category_selected = 0
        for item in groups.get(category, [])[:per_category_scan_limit]:
            if category_selected >= per_category_quota or len(selected) >= max_items:
                break
            if try_select(item):
                category_selected += 1

    remaining = sorted(classified, key=sort_key, reverse=True)
    for item in remaining:
        if len(selected) >= max_items:
            break
        try_select(item)

    selected.sort(key=sort_key, reverse=True)
    return selected


def main() -> None:
    load_dotenv()
    config = load_config()
    site_config = config.get("site", {})
    date = report_date(config)
    logger.info("Starting Daily Industry Radar for %s", date)

    try:
        raw_items = fetch_all(config)
        logger.info("Fetched %s raw items", len(raw_items))
    except Exception:
        logger.exception("Fetching failed; empty report will be generated")
        raw_items = []

    unique_items = deduplicate_items(raw_items)
    logger.info("Kept %s items after deduplication", len(unique_items))

    max_items = int(site_config.get("max_items", 40))
    items = enrich_items(unique_items, max_items)
    logger.info("Prepared %s final items", len(items))

    write_pages(
        items=items,
        report_date=date,
        site_title=site_config.get("title", "Daily Industry Radar"),
        top_count=int(site_config.get("top_count", 5)),
    )
    append_news_archive(items, date, Path("data/news_archive.csv"))
    write_markdown_backup(items, date, Path(f"reports/{date}.md"))
    logger.info("Generated site/index.html, archive page, CSV archive, and Markdown backup")


if __name__ == "__main__":
    main()
