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
from modules.insights import apply_radar_scores, assign_value_tiers, build_radar_context
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
MAX_ITEMS_PER_CATEGORY = 5


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


def _classify_and_score(items: list[dict]) -> list[dict]:
    scored: list[dict] = []
    for item in items:
        classification = classify_item(
            item.get("title", ""),
            item.get("summary_raw", ""),
            item.get("category_hint"),
        )
        item["category"] = classification.category
        item["importance_score"] = classification.importance_score
        apply_radar_scores(item)
        scored.append(item)

    for category in CATEGORY_ORDER:
        logger.info(
            "Classified %s items as %s",
            sum(1 for item in scored if item.get("category") == category),
            category,
        )
    return scored


def _select_radar_items(scored: list[dict], max_items: int) -> list[dict]:
    ranked = sorted(
        scored,
        key=lambda item: (int(item.get("total_value_score", 0)), item.get("published_at", "")),
        reverse=True,
    )
    scan_limit = min(len(ranked), max(80, max_items * 4))
    candidates = ranked[:scan_limit]
    selected: list[dict] = []
    selected_urls: set[str] = set()

    def try_select(item: dict, require_source_text: bool = True) -> bool:
        if len(selected) >= max_items:
            return False
        url = item.get("url", "")
        if url in selected_urls:
            return False
        high_value = int(item.get("total_value_score", 0)) >= 72
        if require_source_text and not high_value:
            return False
        has_source_text = has_enough_source_text(item) if require_source_text else False
        if require_source_text and not has_source_text and not high_value:
            logger.info("Skipping low-context item: %s", item.get("title", ""))
            return False
        if require_source_text and not has_source_text:
            logger.info("Using RSS/search excerpt fallback for: %s", item.get("title", ""))
        selected.append(summarize_item(item))
        if url:
            selected_urls.add(url)
        return True

    for item in candidates:
        try_select(item, require_source_text=True)
        if len(selected) >= max_items:
            break

    for item in candidates:
        try_select(item, require_source_text=False)
        if len(selected) >= max_items:
            break

    return assign_value_tiers(selected)


def enrich_items(items: list[dict], max_items: int) -> list[dict]:
    scored = _classify_and_score(items)
    return _select_radar_items(scored, max_items)


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
    radar_context = build_radar_context(items)
    logger.info("Prepared %s final radar items", len(items))

    write_pages(
        items=items,
        report_date=date,
        site_title=site_config.get("title", "Daily Industry Radar"),
        top_count=int(site_config.get("top_count", 5)),
        radar_context=radar_context,
    )
    append_news_archive(items, date, Path("data/news_archive.csv"))
    write_markdown_backup(items, date, Path(f"reports/{date}.md"), radar_context=radar_context)
    logger.info("Generated site/index.html, archive page, CSV archive, and Markdown backup")


if __name__ == "__main__":
    main()
