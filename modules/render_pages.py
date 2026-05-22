from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

from modules.classifier import CATEGORY_LABELS


CATEGORY_ORDER = [
    "cross_border_ecommerce",
    "furniture_home",
    "ai_tech",
    "consumer_retail",
    "others",
]


STYLE = """
:root{color-scheme:light;--bg:#f6f7f9;--card:#fff;--text:#17202a;--muted:#667085;--line:#e5e7eb;--accent:#0f766e;--accent2:#7c3aed}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif;font-size:16px;line-height:1.6}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{width:min(960px,100%);margin:0 auto;padding:20px 14px 44px}
header{padding:12px 2px 18px}h1{margin:0;font-size:30px;line-height:1.15;letter-spacing:0}.date{margin-top:8px;color:var(--muted);font-size:15px}
.section{margin-top:22px}.section h2{font-size:21px;margin:0 0 12px}.top{display:grid;gap:10px}
.top-item{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.top-item strong{display:block;font-size:16px;line-height:1.35}.top-item span{display:block;color:var(--muted);font-size:14px;margin-top:6px}
.grid{display:grid;gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:9px}.pill{font-size:12px;line-height:1;border-radius:999px;padding:6px 8px;background:#eef6f5;color:#0f766e}.score{background:#f1ecfe;color:#6d28d9}
.card h3{margin:0 0 8px;font-size:18px;line-height:1.35}.one{font-weight:650;margin:0 0 8px}.summary,.why{margin:0 0 8px;color:#344054}.why b{color:#1f2937}
.source{color:var(--muted);font-size:13px;margin-top:10px}.empty{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px;color:var(--muted)}
.archive-list{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}.archive-list li{padding:8px 0;border-bottom:1px solid var(--line)}.archive-list li:last-child{border-bottom:0}
footer{margin-top:30px;color:var(--muted);font-size:13px}
@media (min-width:760px){.wrap{padding:28px 22px 56px}.grid{grid-template-columns:1fr 1fr}h1{font-size:38px}}
"""


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="wrap">{body}</main>
</body>
</html>
"""


def select_top_items(items: list[dict], count: int = 5) -> list[dict]:
    selected: list[dict] = []
    used_categories: set[str] = set()
    sorted_items = sorted(items, key=lambda x: int(x.get("importance_score", 1)), reverse=True)
    for item in sorted_items:
        if item.get("category") not in used_categories:
            selected.append(item)
            used_categories.add(item.get("category", "others"))
        if len(selected) >= count:
            return selected
    for item in sorted_items:
        if item not in selected:
            selected.append(item)
        if len(selected) >= count:
            break
    return selected


def _card(item: dict) -> str:
    category = item.get("category", "others")
    return f"""
<article class="card">
  <div class="meta">
    <span class="pill">{escape(CATEGORY_LABELS.get(category, "其他观察"))}</span>
    <span class="pill score">重要性 {escape(str(item.get("importance_score", "1")))}/5</span>
  </div>
  <h3>{escape(item.get("title", ""))}</h3>
  <p class="one">{escape(item.get("one_sentence", ""))}</p>
  <p class="summary">{escape(item.get("summary", ""))}</p>
  <p class="why"><b>为什么值得关注：</b>{escape(item.get("why_it_matters", ""))}</p>
  <div class="source">{escape(item.get("source_name", ""))} · {escape(item.get("published_at", ""))} · <a href="{escape(item.get("url", ""))}" rel="noopener noreferrer" target="_blank">原文链接</a></div>
</article>
"""


def render_daily_page(items: list[dict], report_date: str, title: str, top_count: int = 5) -> str:
    top_items = select_top_items(items, top_count)
    top_html = "".join(
        f'<div class="top-item"><strong>{escape(item.get("title", ""))}</strong><span>{escape(item.get("one_sentence", ""))}</span></div>'
        for item in top_items
    )
    if not items:
        top_html = '<div class="empty">今日未抓取到符合条件的资讯，请检查信息源或关键词配置。</div>'

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item.get("category", "others")].append(item)

    sections = []
    for category in CATEGORY_ORDER:
        cards = "".join(_card(item) for item in grouped.get(category, []))
        if cards:
            sections.append(f'<section class="section"><h2>{CATEGORY_LABELS[category]}</h2><div class="grid">{cards}</div></section>')

    body = f"""
<header>
  <h1>{escape(title)}</h1>
  <div class="date">{escape(report_date)} · 面向公开资讯的中性摘要</div>
</header>
<section class="section">
  <h2>今日重点 Top {top_count}</h2>
  <div class="top">{top_html}</div>
</section>
{''.join(sections)}
<footer>所有内容均基于公开标题、来源、发布时间和原文链接生成；请以原文为准。</footer>
"""
    return _html_page(f"{title} - {report_date}", body)


def render_archive_index(archive_dir: Path, title: str) -> str:
    pages = sorted([p for p in archive_dir.glob("*.html") if p.name != "index.html"], reverse=True)
    items = "".join(f'<li><a href="{page.name}">{page.stem}</a></li>' for page in pages)
    if not items:
        items = "<li>暂无历史日报</li>"
    body = f"""
<header>
  <h1>{escape(title)} 历史日报</h1>
  <div class="date">更新于 {escape(datetime.now().strftime("%Y-%m-%d %H:%M"))}</div>
</header>
<ul class="archive-list">{items}</ul>
<footer><a href="../index.html">返回最新日报</a></footer>
"""
    return _html_page(f"{title} Archive", body)


def write_pages(items: list[dict], report_date: str, site_title: str, top_count: int) -> None:
    site_dir = Path("site")
    archive_dir = site_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    html = render_daily_page(items, report_date, site_title, top_count)
    (site_dir / "index.html").write_text(html, encoding="utf-8")
    (archive_dir / f"{report_date}.html").write_text(html, encoding="utf-8")
    (archive_dir / "index.html").write_text(render_archive_index(archive_dir, site_title), encoding="utf-8")
