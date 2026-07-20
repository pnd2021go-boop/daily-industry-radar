from __future__ import annotations

from datetime import datetime
from hashlib import sha1
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

STYLE = """
:root{color-scheme:light dark;--bg:#edf1f5;--surface:#f8fafc;--surface-2:#e7edf4;--ink:#17202b;--muted:#586678;--line:#cbd5e1;--accent:#1659c7;--accent-soft:#dce9ff;--focus:#0d49a8;--good:#235b45;--warn:#8a5414;--danger:#9b3030;--radius:12px;--shadow:0 12px 34px rgba(43,56,76,.09)}
@media(prefers-color-scheme:dark){:root{--bg:#101720;--surface:#18222d;--surface-2:#202d3a;--ink:#eef3f8;--muted:#a8b5c4;--line:#364555;--accent:#76a8ff;--accent-soft:#203a63;--focus:#9bc0ff;--good:#8cc7aa;--warn:#e0b16e;--danger:#ef9999;--shadow:0 12px 34px rgba(0,0,0,.2)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:linear-gradient(145deg,var(--surface-2),var(--bg) 28rem);color:var(--ink);font-family:"Avenir Next","Noto Sans SC","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.62}button,input{font:inherit}button,a{touch-action:manipulation}a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}a:hover{text-decoration-thickness:2px}:focus-visible{outline:3px solid var(--focus);outline-offset:3px}.wrap{width:min(1180px,100%);margin:0 auto;padding:18px 14px 56px}.hero{min-height:270px;display:grid;align-content:end;background:#162b48;color:#f4f7fb;border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);position:relative;overflow:hidden}.hero:before{content:"";position:absolute;inset:0;background:linear-gradient(115deg,transparent 20%,rgba(49,112,211,.3)),repeating-linear-gradient(90deg,transparent 0 79px,rgba(255,255,255,.035) 80px)}.hero>*{position:relative}.hero h1{margin:0;font-size:clamp(30px,7vw,52px);line-height:1.02;letter-spacing:-.035em}.date{margin-top:10px;color:#bccce1;font-family:"SFMono-Regular",Consolas,monospace;font-size:13px}.judgement{max-width:880px;margin:18px 0 0;font-size:clamp(17px,3vw,22px);font-weight:650;line-height:1.42}.tags,.meta,.actions,.filters,.stats{display:flex;flex-wrap:wrap;gap:8px}.tags{margin-top:16px}.tag,.badge{border-radius:999px;padding:5px 9px;font-size:12px;line-height:1.2}.tag{border:1px solid #5d7594;color:#e5eef9;background:#223b5c}.section{margin-top:26px}.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;margin-bottom:11px}.section h2{font-size:21px;line-height:1.2;margin:0;letter-spacing:-.015em}.section-note{color:var(--muted);font-size:12px}.brief{border-left:4px solid var(--accent);background:var(--surface);border-radius:0 var(--radius) var(--radius) 0;padding:16px 18px;box-shadow:var(--shadow)}.brief p{margin:0}.brief p+p{margin-top:7px}.toolbar{position:sticky;top:8px;z-index:5;margin-top:18px;background:color-mix(in srgb,var(--surface) 92%,transparent);border:1px solid var(--line);border-radius:var(--radius);padding:12px;box-shadow:var(--shadow);backdrop-filter:blur(14px)}.search{width:100%;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);padding:10px 12px}.filters{margin-top:10px}.filter,.action-btn,.dialog-btn{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:8px;padding:7px 10px;cursor:pointer;white-space:nowrap}.filter[aria-pressed="true"],.filter:hover,.action-btn:hover,.dialog-btn:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}.filter:active,.action-btn:active,.dialog-btn:active{transform:translateY(1px)}.stats{margin-top:9px;color:var(--muted);font-size:12px}.grid{display:grid;gap:12px}.grid.two{grid-template-columns:1fr}.intel-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:17px;box-shadow:0 5px 18px rgba(43,56,76,.05)}.intel-card.must{border-top:4px solid var(--accent)}.intel-card.hidden{display:none}.intel-card h3{margin:9px 0 11px;font-size:18px;line-height:1.38}.badge{background:var(--surface-2);color:var(--muted);font-weight:650}.badge.authority{background:var(--accent-soft);color:var(--accent)}.badge.us{background:var(--accent);color:var(--surface)}.badge.total{color:var(--good)}.facts{margin:0;color:var(--ink);font-size:15px}.relevance{margin:13px 0 0;padding:10px 12px;border-left:3px solid var(--accent);background:var(--accent-soft);color:var(--ink);font-weight:620}.analysis{margin-top:13px;border-top:1px solid var(--line);padding-top:10px}.analysis summary{cursor:pointer;color:var(--accent);font-weight:700}.field{margin-top:11px}.label{margin:0 0 3px;color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.05em}.text{margin:0}.source-row{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-top:14px;color:var(--muted);font-size:12px}.source-row .source-name{color:var(--ink);font-weight:750}.actions{margin-top:14px}.action-btn.saved{background:var(--accent);border-color:var(--accent);color:var(--surface)}.transfer{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px}.transfer h3{margin:0;font-size:17px}.related{margin:9px 0 0;padding-left:20px}.related li+li{margin-top:5px}.weak{border-left:4px solid var(--warn)}.archive{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:13px 15px}.archive>summary{cursor:pointer;font-weight:800}.archive-section{margin-top:16px}.archive-section h3{font-size:15px}.mini-list{display:grid;gap:8px}.mini{background:var(--bg);border-radius:9px;padding:11px}.mini-title{font-weight:700}.mini-meta{color:var(--muted);font-size:12px;margin-top:5px}.empty{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:18px;color:var(--muted)}footer{margin-top:30px;color:var(--muted);font-size:12px}.toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:20;background:var(--ink);color:var(--surface);padding:9px 13px;border-radius:8px;box-shadow:var(--shadow)}.toast[hidden]{display:none}dialog{width:min(680px,calc(100% - 24px));max-height:80dvh;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);color:var(--ink);padding:0;box-shadow:var(--shadow)}dialog::backdrop{background:rgba(10,18,28,.58)}.dialog-head{position:sticky;top:0;background:var(--surface);display:flex;justify-content:space-between;align-items:center;gap:12px;padding:15px;border-bottom:1px solid var(--line)}.dialog-head h2{margin:0;font-size:20px}.saved-list{display:grid;gap:10px;padding:15px}.saved-item{background:var(--bg);border-radius:9px;padding:12px}.saved-item h3{font-size:15px;margin:0 0 5px}.saved-item p{font-size:13px;margin:5px 0;color:var(--muted)}.dialog-actions{display:flex;gap:8px;padding:0 15px 15px}.no-results{margin-top:14px}
@media(min-width:760px){.wrap{padding:28px 24px 68px}.hero{padding:32px}.toolbar{display:grid;grid-template-columns:minmax(260px,1fr) auto;align-items:start;column-gap:12px}.toolbar .search{grid-row:1/3}.filters{margin-top:0;justify-content:flex-end}.stats{justify-content:flex-end}.grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.intel-card{padding:19px}.section{margin-top:32px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
"""

SCRIPT = r"""
(() => {
  const storageKey = 'daily-industry-radar:saved:v1';
  const cards = [...document.querySelectorAll('[data-intel-card]')];
  const filters = [...document.querySelectorAll('[data-filter]')];
  const search = document.querySelector('#radar-search');
  const count = document.querySelector('#visible-count');
  const savedCount = document.querySelector('#saved-count');
  const dialog = document.querySelector('#saved-dialog');
  const toast = document.querySelector('#toast');
  let activeFilter = 'all';

  const readSaved = () => {
    try { return JSON.parse(localStorage.getItem(storageKey) || '{}'); }
    catch { return {}; }
  };
  const writeSaved = value => localStorage.setItem(storageKey, JSON.stringify(value));
  const announce = message => {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    window.setTimeout(() => { toast.hidden = true; }, 1800);
  };
  const payloadFrom = button => ({
    id: button.dataset.id,
    title: button.dataset.title,
    url: button.dataset.url,
    source: button.dataset.source,
    date: button.dataset.date,
    summary: button.dataset.summary,
    relevance: button.dataset.relevance
  });
  const shareText = item => `${item.title}\n\n资讯摘要：${item.summary}\n\n与我的相关性：${item.relevance}\n\n来源：${item.source}\n${item.url}`;

  function syncSavedUI() {
    const saved = readSaved();
    document.querySelectorAll('[data-save]').forEach(button => {
      const on = Boolean(saved[button.dataset.id]);
      button.classList.toggle('saved', on);
      button.setAttribute('aria-pressed', String(on));
      button.textContent = on ? '已收藏' : '收藏';
    });
    if (savedCount) savedCount.textContent = String(Object.keys(saved).length);
    renderSavedDialog(saved);
  }

  function applyFilters() {
    const term = (search?.value || '').trim().toLowerCase();
    const saved = readSaved();
    let visible = 0;
    cards.forEach(card => {
      const matchesText = !term || card.textContent.toLowerCase().includes(term);
      const matchesFilter = activeFilter === 'all'
        || card.dataset.tier === activeFilter
        || card.dataset.category === activeFilter
        || (activeFilter === 'us' && card.dataset.us === 'true')
        || (activeFilter === 'saved' && Boolean(saved[card.dataset.id]));
      const show = matchesText && matchesFilter;
      card.classList.toggle('hidden', !show);
      if (show) visible += 1;
    });
    if (count) count.textContent = String(visible);
    const noResults = document.querySelector('#no-results');
    if (noResults) noResults.hidden = visible !== 0;
  }

  function renderSavedDialog(saved) {
    const list = document.querySelector('#saved-list');
    if (!list) return;
    const items = Object.values(saved).reverse();
    list.innerHTML = items.length ? items.map(item => `
      <article class="saved-item">
        <h3><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a></h3>
        <p>${escapeHtml(item.source)} · ${escapeHtml(item.date)}</p>
        <p>${escapeHtml(item.summary)}</p>
        <button class="dialog-btn" data-remove-saved="${escapeHtml(item.id)}">移出收藏</button>
      </article>`).join('') : '<div class="empty">还没有收藏资讯。你可以在任意新闻卡片上点击“收藏”。</div>';
  }

  function escapeHtml(value = '') {
    return value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }

  filters.forEach(button => button.addEventListener('click', () => {
    activeFilter = button.dataset.filter;
    filters.forEach(candidate => candidate.setAttribute('aria-pressed', String(candidate === button)));
    applyFilters();
  }));
  search?.addEventListener('input', applyFilters);

  document.addEventListener('click', async event => {
    const saveButton = event.target.closest('[data-save]');
    if (saveButton) {
      const saved = readSaved();
      const item = payloadFrom(saveButton);
      if (saved[item.id]) { delete saved[item.id]; announce('已移出收藏'); }
      else { saved[item.id] = item; announce('已加入收藏'); }
      writeSaved(saved); syncSavedUI(); applyFilters();
      return;
    }
    const shareButton = event.target.closest('[data-share]');
    if (shareButton) {
      const item = payloadFrom(shareButton);
      try {
        if (navigator.share) await navigator.share({title:item.title, text:shareText(item), url:item.url});
        else { await navigator.clipboard.writeText(shareText(item)); announce('转发文本已复制'); }
      } catch (error) {
        if (error.name !== 'AbortError') announce('转发失败，请打开原文后分享');
      }
      return;
    }
    const removeButton = event.target.closest('[data-remove-saved]');
    if (removeButton) {
      const saved = readSaved(); delete saved[removeButton.dataset.removeSaved]; writeSaved(saved);
      syncSavedUI(); applyFilters(); announce('已移出收藏');
    }
  });

  document.querySelector('#open-saved')?.addEventListener('click', () => dialog?.showModal());
  document.querySelector('#close-saved')?.addEventListener('click', () => dialog?.close());
  document.querySelector('#copy-saved')?.addEventListener('click', async () => {
    const items = Object.values(readSaved());
    if (!items.length) { announce('收藏夹为空'); return; }
    await navigator.clipboard.writeText(items.map(shareText).join('\n\n----------------\n\n'));
    announce('收藏清单已复制');
  });
  syncSavedUI(); applyFilters();
})();
"""


def _html_page(title: str, body: str) -> str:
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#162b48">
  <title>{escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="wrap">{body}</main>
  <div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
  <script>{SCRIPT}</script>
</body>
</html>
"""
    return html.replace("—", "-")


def _item_id(item: dict) -> str:
    value = item.get("url") or item.get("title", "")
    return sha1(value.encode("utf-8")).hexdigest()[:16]


def _score_badges(item: dict) -> str:
    return "".join([
        f'<span class="badge total">价值 {escape(str(item.get("total_value_score", 0)))}</span>',
        f'<span class="badge">业务 {escape(str(item.get("business_relevance_score", "-")))}/5</span>',
        f'<span class="badge">迁移 {escape(str(item.get("knowledge_transfer_score", "-")))}/5</span>',
        f'<span class="badge">行动 {escape(str(item.get("actionability_score", "-")))}/5</span>',
    ])


def _category_badge(item: dict) -> str:
    label = CATEGORY_LABELS.get(item.get("category", "others"), "其他观察")
    return f'<span class="badge">{escape(label)}</span>'


def _source_badges(item: dict) -> str:
    us = '<span class="badge us">美国优先</span>' if item.get("is_us_priority") else ""
    authority = escape(item.get("source_authority_label", "权威来源"))
    context = escape(item.get("source_context_label", "信息有限"))
    summary_label = escape(item.get("summary_generation_label", "原文事实摘录"))
    return f'<span class="badge authority">{authority}</span>{us}<span class="badge">{context}</span><span class="badge">{summary_label}</span>'


def _field(label: str, value: str) -> str:
    if not value:
        return ""
    return f'<div class="field"><div class="label">{escape(label)}</div><p class="text">{escape(value)}</p></div>'


def _data_attrs(item: dict) -> str:
    values = {
        "id": _item_id(item),
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source_name", ""),
        "date": item.get("published_at", ""),
        "summary": item.get("summary_zh") or item.get("summary", ""),
        "relevance": item.get("relevance_reason", ""),
    }
    return " ".join(f'data-{key}="{escape(str(value), quote=True)}"' for key, value in values.items())


def _action_buttons(item: dict) -> str:
    attrs = _data_attrs(item)
    url = escape(item.get("url", ""), quote=True)
    return f"""
<div class="actions">
  <a class="action-btn" href="{url}" rel="noopener noreferrer" target="_blank">阅读原文</a>
  <button class="action-btn" type="button" data-save {attrs} aria-pressed="false">收藏</button>
  <button class="action-btn" type="button" data-share {attrs}>转发</button>
</div>"""


def _insight_card(item: dict, tier: str, extra_class: str = "") -> str:
    card_id = _item_id(item)
    classes = " ".join(value for value in ["intel-card", "must" if tier == "must_read" else "", extra_class] if value)
    return f"""
<article class="{classes}" data-intel-card data-id="{card_id}" data-tier="{escape(tier)}" data-category="{escape(item.get('category', 'others'))}" data-us="{str(bool(item.get('is_us_priority'))).lower()}">
  <div class="meta">{_source_badges(item)}{_category_badge(item)}{_score_badges(item)}</div>
  <h3>{escape(item.get("title", ""))}</h3>
  <p class="facts">{escape(item.get("summary_zh") or item.get("summary", ""))}</p>
  <p class="relevance">{escape(item.get("relevance_reason", ""))}</p>
  <details class="analysis" {'open' if tier == 'must_read' else ''}>
    <summary>查看判断与建议</summary>
    {_field("为什么重要", item.get("why_it_matters", ""))}
    {_field("业务影响", item.get("business_implication", ""))}
    {_field("知识迁移", item.get("knowledge_transfer", ""))}
    {_field("建议动作", item.get("suggested_action", ""))}
  </details>
  <div class="source-row"><span class="source-name">{escape(item.get("source_name", ""))}</span><span>{escape(item.get("published_at", ""))}</span></div>
  {_action_buttons(item)}
</article>
"""


def _transfer_card(card: dict) -> str:
    related = "".join(
        f'<li><a href="{escape(item.get("url", ""), quote=True)}" rel="noopener noreferrer" target="_blank">{escape(item.get("title", ""))}</a></li>'
        for item in card.get("related_news", [])
    )
    return f"""
<article class="transfer">
  <h3>{escape(card.get("theme_name", ""))}</h3>
  {_field("发生了什么", card.get("what_happened", ""))}
  {_field("为什么重要", card.get("why_important", ""))}
  {_field("可迁移到哪里", card.get("transfer_to", ""))}
  {_field("对 ModernMate / Radar / Echo 的启发", card.get("inspiration", ""))}
  {_field("可以尝试的一个小动作", card.get("small_action", ""))}
  <div class="label">关联新闻</div><ul class="related">{related}</ul>
</article>
"""


def _weak_signal(signal: dict) -> str:
    item = dict(signal.get("item", {}))
    item["why_it_matters"] = signal.get("why_weak", "")
    item["business_implication"] = signal.get("watch_next", "")
    return _insight_card(item, "weak_signals", "weak")


def _mini_item(item: dict) -> str:
    return f"""
<article class="mini">
  <div class="mini-title"><a href="{escape(item.get("url", ""), quote=True)}" rel="noopener noreferrer" target="_blank">{escape(item.get("title", ""))}</a></div>
  <div class="mini-meta">{escape(item.get("source_name", ""))} · 价值 {escape(str(item.get("total_value_score", "")))}</div>
  {_action_buttons(item)}
</article>"""


def _archive_html(items: list[dict]) -> str:
    grouped = grouped_archive(items)
    sections = []
    for category in CATEGORY_ORDER:
        category_items = grouped.get(category, [])
        if category_items:
            cards = "".join(_mini_item(item) for item in category_items)
            sections.append(f'<div class="archive-section"><h3>{escape(CATEGORY_LABELS[category])} · {len(category_items)} 条</h3><div class="mini-list">{cards}</div></div>')
    return f'<details class="archive"><summary>全部权威资讯归档，按原始分类查看</summary>{"".join(sections)}</details>' if sections else '<div class="empty">暂无归档资讯。</div>'


def _toolbar(items: list[dict]) -> str:
    visible_items = sum(1 for item in items if item.get("value_tier") in {"must_read", "worth_scanning", "weak_signals"})
    return f"""
<nav class="toolbar" aria-label="资讯筛选与处理工具">
  <label><span class="label">搜索资讯</span><input id="radar-search" class="search" type="search" placeholder="搜索平台、品牌、品类或主题"></label>
  <div class="filters">
    <button class="filter" type="button" data-filter="all" aria-pressed="true">全部</button>
    <button class="filter" type="button" data-filter="must_read" aria-pressed="false">必读</button>
    <button class="filter" type="button" data-filter="worth_scanning" aria-pressed="false">快读</button>
    <button class="filter" type="button" data-filter="weak_signals" aria-pressed="false">弱信号</button>
    <button class="filter" type="button" data-filter="us" aria-pressed="false">美国来源</button>
    <button class="filter" type="button" data-filter="saved" aria-pressed="false">本页收藏</button>
    <button id="open-saved" class="filter" type="button">收藏夹 <span id="saved-count">0</span></button>
  </div>
  <div class="stats"><span>当前显示 <strong id="visible-count">{visible_items}</strong> 条</span><span>主推送只收录权威来源</span></div>
</nav>
<div id="no-results" class="empty no-results" hidden>没有符合当前筛选条件的资讯。</div>
"""


def _saved_dialog() -> str:
    return """
<dialog id="saved-dialog">
  <div class="dialog-head"><h2>我的收藏夹</h2><button id="close-saved" class="dialog-btn" type="button">关闭</button></div>
  <div id="saved-list" class="saved-list"></div>
  <div class="dialog-actions"><button id="copy-saved" class="dialog-btn" type="button">复制收藏清单</button></div>
</dialog>
"""


def render_daily_page(items: list[dict], report_date: str, title: str, top_count: int = 5, radar_context: dict | None = None) -> str:
    radar_context = radar_context or {}
    executive = radar_context.get("executive_brief", {})
    tags_html = "".join(f'<span class="tag">{escape(str(tag))}</span>' for tag in executive.get("keywords", []))
    brief_html = "".join(f'<p>{escape(sentence)}</p>' for sentence in executive.get("sentences", [])) or '<p>今日未抓取到符合权威来源和业务相关性门槛的资讯。</p>'
    must_items = tier_items(items, "must_read")[:3]
    worth_items = tier_items(items, "worth_scanning")[:5]
    must_html = "".join(_insight_card(item, "must_read") for item in must_items) or '<div class="empty">今天没有达到必读门槛的资讯。</div>'
    worth_html = "".join(_insight_card(item, "worth_scanning") for item in worth_items) or '<div class="empty">今天没有额外的快读资讯。</div>'
    transfer_html = "".join(_transfer_card(card) for card in radar_context.get("knowledge_cards", [])) or '<div class="empty">今天暂未形成稳定的知识迁移主题。</div>'
    weak_html = "".join(_weak_signal(signal) for signal in radar_context.get("weak_signals", [])[:5]) or '<div class="empty">今天没有需要单独标记的弱信号。</div>'

    body = f"""
<header class="hero">
  <h1>{escape(title)}</h1>
  <div class="date">{escape(report_date)} · 美国权威来源优先 · 每日业务情报</div>
  <p class="judgement">{escape(executive.get("judgement", "今天已完成权威来源筛选，请优先阅读事实摘要与相关性判断。"))}</p>
  <div class="tags">{tags_html}</div>
</header>
{_toolbar(items)}
<section class="section"><div class="section-head"><h2>今日判断</h2><span class="section-note">先读结论，再进入新闻</span></div><div class="brief">{brief_html}</div></section>
<section class="section"><div class="section-head"><h2>今日必读</h2><span class="section-note">事实、相关性与建议完整展开</span></div><div class="grid">{must_html}</div></section>
<section class="section"><div class="section-head"><h2>主题洞察</h2><span class="section-note">跨新闻的知识迁移</span></div><div class="grid two">{transfer_html}</div></section>
<section class="section"><div class="section-head"><h2>值得快读</h2><span class="section-note">最多 5 条</span></div><div class="grid two">{worth_html}</div></section>
<section class="section"><div class="section-head"><h2>弱信号</h2><span class="section-note">等待连续证据</span></div><div class="grid two">{weak_html}</div></section>
<section class="section">{_archive_html(items)}</section>
{_saved_dialog()}
<footer>页面仅收录权威媒体、行业垂直媒体、机构研究和官方来源。收藏保存在当前浏览器；转发会携带标题、事实摘要、相关性和原文链接。</footer>
"""
    return _html_page(f"{title} - {report_date}", body)


def render_archive_index(archive_dir: Path, title: str) -> str:
    pages = sorted([p for p in archive_dir.glob("*.html") if p.name != "index.html"], reverse=True)
    items = "".join(f'<li><a href="{page.name}">{page.stem}</a></li>' for page in pages) or "<li>暂无历史日报</li>"
    body = f'<header class="hero"><h1>{escape(title)} 历史日报</h1><div class="date">更新于 {escape(datetime.now().strftime("%Y-%m-%d %H:%M"))}</div></header><ul>{items}</ul><footer><a href="../index.html">返回最新日报</a></footer>'
    return _html_page(f"{title} Archive", body)


def write_pages(items: list[dict], report_date: str, site_title: str, top_count: int, radar_context: dict | None = None) -> None:
    site_dir = Path("site")
    archive_dir = site_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    html = render_daily_page(items, report_date, site_title, top_count, radar_context=radar_context)
    (site_dir / "index.html").write_text(html, encoding="utf-8")
    (archive_dir / f"{report_date}.html").write_text(html, encoding="utf-8")
    (archive_dir / "index.html").write_text(render_archive_index(archive_dir, site_title), encoding="utf-8")
