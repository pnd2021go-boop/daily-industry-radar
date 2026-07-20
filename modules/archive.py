from __future__ import annotations

import csv
from pathlib import Path

from modules.insights import tier_items


FIELDNAMES = [
    "date", "title", "one_sentence", "summary_zh", "why_it_matters", "business_implication",
    "knowledge_transfer", "suggested_action", "noise_reason", "category", "value_tier",
    "business_relevance_score", "knowledge_transfer_score", "actionability_score",
    "source_quality_score", "total_value_score", "source_name", "source_authority_label",
    "is_us_priority", "source_context_score", "source_context_label", "summary_generation_label",
    "summary_substantive", "relevance_reason", "published_at", "url",
]

INTEGER_FIELDS = {
    "business_relevance_score", "knowledge_transfer_score", "actionability_score",
    "source_quality_score", "total_value_score", "source_context_score",
}
BOOLEAN_FIELDS = {"is_us_priority", "summary_substantive"}


def load_news_archive(path: Path, report_date: str) -> list[dict]:
    """Load the last successful same-day snapshot for transient feed failures."""
    if not path.exists():
        return []
    items: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("date") != report_date or not row.get("url"):
                continue
            item = dict(row)
            for field in INTEGER_FIELDS:
                try:
                    item[field] = int(item.get(field) or 0)
                except ValueError:
                    item[field] = 0
            for field in BOOLEAN_FIELDS:
                item[field] = str(item.get(field, "")).lower() in {"1", "true", "yes"}
            item["summary"] = item.get("summary_zh", "")
            item["is_authoritative_source"] = True
            items.append(item)
    return items


def append_news_archive(items: list[dict], report_date: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_urls: set[str] = set()
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            existing_urls = {row.get("url", "") for row in csv.DictReader(f)}

    write_header = not path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        for item in items:
            if item.get("url") in existing_urls:
                continue
            row = {field: item.get(field, "") for field in FIELDNAMES}
            row["date"] = report_date
            writer.writerow(row)


def _score_line(item: dict) -> str:
    return (
        f"- 分数：总分 {item.get('total_value_score', '')}；"
        f"业务 {item.get('business_relevance_score', '')}/5；"
        f"迁移 {item.get('knowledge_transfer_score', '')}/5；"
        f"行动 {item.get('actionability_score', '')}/5；"
        f"来源 {item.get('source_quality_score', '')}/5"
    )


def write_markdown_backup(items: list[dict], report_date: str, path: Path, radar_context: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    radar_context = radar_context or {}
    executive = radar_context.get("executive_brief", {})
    lines = [f"# Daily Industry Radar - {report_date}", ""]
    if executive.get("judgement"):
        lines.extend([f"> {executive.get('judgement')}", ""])
    for sentence in executive.get("sentences", []):
        lines.extend([f"- {sentence}"])
    if executive.get("sentences"):
        lines.append("")

    if not items:
        lines.append("今日未抓取到符合条件的资讯，请检查信息源或关键词配置。")

    sections = [
        ("Must Read", tier_items(items, "must_read")),
        ("Worth Scanning", tier_items(items, "worth_scanning")),
        ("Weak Signals", tier_items(items, "weak_signals")),
        ("Archive", tier_items(items, "archive")),
    ]
    for section_title, section_items in sections:
        if not section_items:
            continue
        lines.extend([f"## {section_title}", ""])
        for item in section_items:
            lines.extend([
                f"### {item.get('title', '')}",
                "",
                f"- 分类：{item.get('category', '')}",
                f"- 层级：{item.get('value_tier', '')}",
                _score_line(item),
                f"- 来源：{item.get('source_name', '')}",
                f"- 发布时间：{item.get('published_at', '')}",
                f"- 原文链接：{item.get('url', '')}",
                "",
                f"**摘要**：{item.get('summary_zh') or item.get('summary', '')}",
                "",
                f"**为什么重要**：{item.get('why_it_matters', '')}",
                "",
                f"**业务影响**：{item.get('business_implication', '')}",
                "",
                f"**知识迁移**：{item.get('knowledge_transfer', '')}",
                "",
                f"**建议动作**：{item.get('suggested_action', '')}",
                "",
            ])
            if item.get("noise_reason"):
                lines.extend([f"**降权原因**：{item.get('noise_reason', '')}", ""])

    cards = radar_context.get("knowledge_cards", [])
    if cards:
        lines.extend(["## Knowledge Transfer Cards", ""])
        for card in cards:
            lines.extend([
                f"### {card.get('theme_name', '')}",
                "",
                f"- 发生了什么：{card.get('what_happened', '')}",
                f"- 为什么重要：{card.get('why_important', '')}",
                f"- 可迁移到：{card.get('transfer_to', '')}",
                f"- 小动作：{card.get('small_action', '')}",
                "",
            ])
    path.write_text("\n".join(lines), encoding="utf-8")
