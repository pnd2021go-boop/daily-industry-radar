from __future__ import annotations

import csv
from pathlib import Path


FIELDNAMES = [
    "date", "title", "one_sentence", "summary", "why_it_matters", "category",
    "importance_score", "source_name", "published_at", "url",
]


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


def write_markdown_backup(items: list[dict], report_date: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Daily Industry Radar - {report_date}", ""]
    if not items:
        lines.append("今日未抓取到符合条件的资讯，请检查信息源或关键词配置。")
    for item in items:
        lines.extend([
            f"## {item.get('title', '')}",
            "",
            f"- 分类：{item.get('category', '')}",
            f"- 重要性：{item.get('importance_score', '')}/5",
            f"- 来源：{item.get('source_name', '')}",
            f"- 发布时间：{item.get('published_at', '')}",
            f"- 原文链接：{item.get('url', '')}",
            "",
            item.get("one_sentence", ""),
            "",
            item.get("summary", ""),
            "",
            f"值得关注：{item.get('why_it_matters', '')}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")
