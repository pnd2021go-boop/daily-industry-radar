from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

from modules.classifier import CATEGORY_LABELS
from modules.insights import grouped_archive, tier_items


CATEGORY_ORDER = [
    "cross_border_ecommerce",
    "furniture_home",
    "ai_tech",
    "consumer_retail",
    "others",
]

TIER_LABELS = {
    "must_read": "Must Read",
    "worth_scanning": "Worth Scanning",
    "weak_signals": "Weak Signals",
    "archive": "Archive",
}

STYLE = """
:root{color-scheme:light;--bg:#f3f1ea;--paper:#fffdf8;--card:#ffffff;--ink:#1f2933;--muted:#667085;--line:#e5dfd2;--soft:#f5efe2;--soft2:#eef4f1;--accent:#0f5f56;--accent2:#9a5b18;--danger:#9f3a38;--score:#344054;--shadow:0 10px 26px rgba(31,41,51,.07)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#fff8e7 0,#f3f1ea 34%,#edf2ef 100%);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"Noto Sans SC",sans-serif;font-size:16px;line-height:1.66}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}.wrap{width:min(1080px,100%);margin:0 auto;padding:18px 14px 52px}
.hero{background:linear-gradient(135deg,#173f3a,#28594f 58%,#8a5a24);color:#fff;border-radius:18px;padding:22px 18px;box-shadow:var(--shadow)}.hero h1{margin:0;font-size:31px;line-height:1.12;letter-spacing:-.02em}.date{margin-top:8px;color:rgba(255,255,255,.78);font-size:14px}.judgement{margin:18px 0 0;font-size:19px;line-height:1.45;font-weight:720;max-width:900px}.tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.tag{border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.12);color:#fff;border-radius:999px;padding:5px 9px;font-size:12px}
.section{margin-top:24px}.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:12px}.section h2{font-size:22px;margin:0;letter-spacing:-.01em}.section-note{color:var(--muted);font-size:13px}.brief{display:grid;gap:10px;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}.brief p{margin:0;color:#344054}
.grid{display:grid;gap:14px}.grid.two{grid-template-columns:1fr}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 4px 16px rgba(31,41,51,.04)}.card.must{border-color:#d5b06a;background:linear-gradient(180deg,#fffdf7,#fff)}.card h3{margin:0 0 10px;font-size:18px;line-height:1.35}.meta{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:10px}.pill{font-size:12px;line-height:1;border-radius:999px;padding:6px 8px;background:var(--soft2);color:var(--accent);font-weight:650}.pill.score{background:#f1f5f9;color:var(--score)}.pill.total{background:#fff2cc;color:#7a4b00}.pill.low{background:#f8e8e7;color:var(--danger)}
.one{font-weight:700;margin:0 0 10px;color:#1f2937}.field{margin-top:12px}.label{margin:0 0 4px;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}.text{margin:0;color:#344054}.source{display:flex;flex-wrap:wrap;gap:7px;color:var(--muted);font-size:13px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}
.transfer{background:linear-gradient(180deg,#ffffff,#fbf7ed);border:1px solid #e6d7bb}.transfer h3{color:#173f3a}.related{margin:12px 0 0;padding-left:18px;color:#475467}.related li{margin:5px 0}.signal{border-left:4px solid var(--accent2)}.empty{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;color:var(--muted)}
details.archive{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:12px 14px}details.archive>summary{cursor:pointer;font-weight:800;font-size:18px}.archive-section{margin-top:14px}.archive-section h3{font-size:16px;margin:14px 0 8px}.mini-list{display:grid;gap:9px}.mini{background:#fff;border:1px solid var(--line);border-radius:10px;padding:11px}.mini-title{font-weight:700}.mini-meta{display:flex;flex-wrap:wrap;gap:7px;color:var(--muted);font-size:12px;margin-top:6px}
.archive-list{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 14px}.archive-list li{padding:8px 0;border-bottom:1px solid var(--line)}.archive-list li:last-child{border-bottom:0}footer{margin-top:30px;color:var(--muted);font-size:13px}
@media (min-width:760px){.wrap{padding:30px 22px 64px}.hero{padding:30px 28px}.hero h1{font-size:42px}.grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.card{padding:18px}.brief{padding:18px}}
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


def _score_badges(item: dict) -> str:
    total = int(item.get("total_value_score", 0) or 0)
    total_class = "total" if total >= 70 else "low" if total < 50 else "score"
    return "".join([
        f'<span class="pill {total_class}">总分 {escape(str(total))}</span>',
        f'<span class="pill score">业务 {escape(str(item.get("business_relevance_score", "-")))}/5</span>',
        f'<span class="pill score">迁移 {escape(str(item.get("knowledge_transfer_score", "-")))}/5</span>',
        f'<span class="pill score">行动 {escape(str(item.get("actionability_score", "-")))}/5</span>',
        f'<span class="pill score">来源 {escape(str(item.get("source_quality_score", "-")))}/5</span>',
    ])


def _category_pill(item: dict) -> str:
    category = item.get("category", "others")
    return f'<span class="pill">{escape(CATEGORY_LABELS.get(category, "其他观察"))}</span>'


def _field(label: str, value: str) -> str:
    if not value:
        return ""
    return f'<div class="field"><div class="label">{escape(label)}</div><p class="text">{escape(value)}</p></div>'


def _insight_card(item: dict, must: bool = False) -> str:
    card_class = "card must" if must else "card"
    return f"""
<article class="{card_class}">
  <div class="meta">{_category_pill(item)}{_score_badges(item)}</div>
  <h3>{escape(item.get("title", ""))}</h3>
  <p class="one">{escape(item.get("one_sentence", ""))}</p>
  {_field("摘要", item.get("summary_zh") or item.get("summary", ""))}
  {_field("为什么值得看", item.get("why_it_matters", ""))}
  {_field("对我的启发", item.get("knowledge_transfer", ""))}
  {_field("建议动作", item.get("suggested_action", ""))}
  <div class="source"><span>{escape(item.get("source_name", ""))}</span><span>{escape(item.get("published_at", ""))}</span><a href="{escape(item.get("url", ""))}" rel="noopener noreferrer" target="_blank">原文链接</a></div>
</article>
"""


def _transfer_card(card: dict) -> str:
    related = "".join(
        f'<li><a href="{escape(item.get("url", ""))}" rel="noopener noreferrer" target="_blank">{escape(item.get("title", ""))}</a></li>'
        for item in card.get("related_news", [])
    )
    return f"""
<article class="card transfer">
  <h3>{escape(card.get("theme_name", ""))}</h3>
  {_field("发生了什么", card.get("what_happened", ""))}
  {_field("为什么重要", card.get("why_important", ""))}
  {_field("可迁移到哪里", card.get("transfer_to", ""))}
  {_field("对 ModernMate / Radar / Echo 的启发", card.get("inspiration", ""))}
  {_field("可以尝试的一个小动作", card.get("small_action", ""))}
  <div class="label">关联新闻</div>
  <ul class="related">{related}</ul>
</article>
"""


def _weak_signal(signal: dict) -> str:
    item = signal.get("item", {})
    return f"""
<article class="card signal">
  <div class="meta">{_category_pill(item)}{_score_badges(item)}</div>
  {_field("信号", signal.get("signal", ""))}
  {_field("为什么暂时只是弱信号", signal.get("why_weak", ""))}
  {_field("后续需要观察什么", signal.get("watch_next", ""))}
  <div class="source"><span>{escape(item.get("source_name", ""))}</span><a href="{escape(item.get("url", ""))}" rel="noopener noreferrer" target="_blank">原文链接</a></div>
</article>
"""


def _mini_item(item: dict) -> str:
    noise = item.get("noise_reason", "")
    noise_html = f'<div class="mini-meta"><span>降权：{escape(noise)}</span></div>' if noise else ""
    return f"""
<div class="mini">
  <div class="mini-title"><a href="{escape(item.get("url", ""))}" rel="noopener noreferrer" target="_blank">{escape(item.get("title", ""))}</a></div>
  <div class="mini-meta"><span>{escape(item.get("source_name", ""))}</span><span>{escape(item.get("published_at", ""))}</span><span>总分 {escape(str(item.get("total_value_score", "")))}</span></div>
  {noise_html}
</div>
"""


def _archive_html(items: list[dict]) -> str:
    grouped = grouped_archive(items)
    sections = []
    for category in CATEGORY_ORDER:
        category_items = grouped.get(category, [])
        if not category_items:
            continue
        mini_items = "".join(_mini_item(item) for item in category_items)
        sections.append(f'<div class="archive-section"><h3>{escape(CATEGORY_LABELS[category])} · {len(category_items)} 条</h3><div class="mini-list">{mini_items}</div></div>')
    if not sections:
        return '<div class="empty">暂无归档资讯。</div>'
    return f'<details class="archive"><summary>原始资讯归档 Archive（默认折叠）</summary>{"".join(sections)}</details>'


def render_daily_page(items: list[dict], report_date: str, title: str, top_count: int = 5, radar_context: dict | None = None) -> str:
    radar_context = radar_context or {}
    executive = radar_context.get("executive_brief", {})
    keywords = executive.get("keywords", [])
    tags_html = "".join(f'<span class="tag">{escape(str(tag))}</span>' for tag in keywords)
    judgement = executive.get("judgement", "今天信息源已更新，请优先阅读高价值条目。")
    brief_sentences = executive.get("sentences", [])
    brief_html = "".join(f'<p>{escape(sentence)}</p>' for sentence in brief_sentences)
    if not brief_html:
        brief_html = '<p>今日未抓取到符合条件的资讯，请检查信息源或关键词配置。</p>'

    must_items = tier_items(items, "must_read")[:3]
    worth_items = tier_items(items, "worth_scanning")[:5]
    transfer_cards = radar_context.get("knowledge_cards", [])
    weak_signals = radar_context.get("weak_signals", [])[:5]

    must_html = "".join(_insight_card(item, must=True) for item in must_items) or '<div class="empty">今天没有达到 Must Read 阈值的资讯。</div>'
    worth_html = "".join(_insight_card(item) for item in worth_items) or '<div class="empty">今天没有额外的 Worth Scanning 条目。</div>'
    transfer_html = "".join(_transfer_card(card) for card in transfer_cards) or '<div class="empty">今天暂未形成稳定的知识迁移主题。</div>'
    weak_html = "".join(_weak_signal(signal) for signal in weak_signals) or '<div class="empty">今天没有需要单独标记的弱信号。</div>'

    body = f"""
<header class="hero">
  <h1>{escape(title)}</h1>
  <div class="date">{escape(report_date)} · 每日行业知识雷达 / 业务洞察看板</div>
  <p class="judgement">{escape(judgement)}</p>
  <div class="tags">{tags_html}</div>
</header>
<section class="section">
  <div class="section-head"><h2>Executive Brief</h2><span class="section-note">3-5 句结构性判断</span></div>
  <div class="brief">{brief_html}</div>
</section>
<section class="section">
  <div class="section-head"><h2>Must Read</h2><span class="section-note">最多 3 条</span></div>
  <div class="grid">{must_html}</div>
</section>
<section class="section">
  <div class="section-head"><h2>Knowledge Transfer Cards</h2><span class="section-note">把新闻转成可迁移洞察</span></div>
  <div class="grid two">{transfer_html}</div>
</section>
<section class="section">
  <div class="section-head"><h2>Worth Scanning</h2><span class="section-note">最多 5 条</span></div>
  <div class="grid two">{worth_html}</div>
</section>
<section class="section">
  <div class="section-head"><h2>Weak Signals</h2><span class="section-note">观察池</span></div>
  <div class="grid two">{weak_html}</div>
</section>
<section class="section">{_archive_html(items)}</section>
<footer>本页面基于公开资讯生成，强调筛选、判断和知识迁移；低价值或证据不足内容会降权进入 Archive。</footer>
"""
    return _html_page(f"{title} - {report_date}", body)


def render_archive_index(archive_dir: Path, title: str) -> str:
    pages = sorted([p for p in archive_dir.glob("*.html") if p.name != "index.html"], reverse=True)
    items = "".join(f'<li><a href="{page.name}">{page.stem}</a></li>' for page in pages)
    if not items:
        items = "<li>暂无历史日报</li>"
    body = f"""
<header class="hero">
  <h1>{escape(title)} 历史日报</h1>
  <div class="date">更新于 {escape(datetime.now().strftime("%Y-%m-%d %H:%M"))}</div>
</header>
<ul class="archive-list">{items}</ul>
<footer><a href="../index.html">返回最新日报</a></footer>
"""
    return _html_page(f"{title} Archive", body)


def write_pages(items: list[dict], report_date: str, site_title: str, top_count: int, radar_context: dict | None = None) -> None:
    site_dir = Path("site")
    archive_dir = site_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    html = render_daily_page(items, report_date, site_title, top_count, radar_context=radar_context)
    (site_dir / "index.html").write_text(html, encoding="utf-8")
    (archive_dir / f"{report_date}.html").write_text(html, encoding="utf-8")
    (archive_dir / "index.html").write_text(render_archive_index(archive_dir, site_title), encoding="utf-8")
