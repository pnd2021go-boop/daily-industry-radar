from __future__ import annotations

import json
import os
import re
from html import unescape

import requests
from bs4 import BeautifulSoup


ARTICLE_TIMEOUT_SECONDS = 4
MAX_ARTICLE_CHARS = 6000
MIN_SOURCE_CHARS = 280
TARGET_SUMMARY_WORDS = 150


def _clean_text(text: str) -> str:
    raw = unescape(text or "")
    if "<" in raw and ">" in raw:
        soup = BeautifulSoup(raw, "html.parser")
        raw = soup.get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", raw).strip()
    return cleaned


def _clip(text: str, limit: int) -> str:
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _article_text_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        response = requests.get(
            url,
            timeout=ARTICLE_TIMEOUT_SECONDS,
            headers={"User-Agent": "DailyIndustryRadar/1.0 (+https://github.com/)"},
        )
        response.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.body
    if not article:
        return ""
    paragraphs = [_clean_text(p.get_text(" ", strip=True)) for p in article.find_all("p")]
    text = " ".join(p for p in paragraphs if len(p) >= 40)
    if not text:
        text = _clean_text(article.get_text(" ", strip=True))
    return _clip(text, MAX_ARTICLE_CHARS)


def _source_text(item: dict) -> str:
    if "article_text" in item:
        article_text = item.get("article_text") or ""
    else:
        article_text = _article_text_from_url(item.get("url", ""))
        item["article_text"] = article_text
    raw = _clean_text(item.get("summary_raw", ""))
    return article_text or raw


def has_enough_source_text(item: dict) -> bool:
    return len(_source_text(item)) >= MIN_SOURCE_CHARS


def _word_count(text: str) -> int:
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    if words:
        return len(words)
    return max(1, len(text) // 2)


def _sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s+", text)
    return [_clean_text(part) for part in parts if _clean_text(part)]


def _is_low_value_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    low_value_terms = [
        "subscribe", "newsletter", "sign up", "follow us", "click here", "advertisement",
        "all rights reserved", "cookie", "privacy policy", "terms of use", "read more",
        "this article is part of", "in our subscribers", "for more on",
    ]
    return any(term in lowered for term in low_value_terms)


def _summary_paragraph(title: str, text: str, source: str) -> str:
    if not text:
        return f"{source} 发布了题为“{title}”的公开资讯，但当前信息源没有提供足够正文内容。"

    sentences = [
        sentence for sentence in _sentence_split(text)
        if len(sentence) >= 40 and not _is_low_value_sentence(sentence)
    ]
    if not sentences:
        return _clip(text, 900)

    title_terms = {
        term.lower()
        for term in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,}", title)
        if len(term) >= 3
    }
    scored = []
    for index, sentence in enumerate(sentences):
        lowered = sentence.lower()
        score = max(0, 8 - index)
        score += sum(4 for term in title_terms if term in lowered)
        score += sum(2 for term in ["said", "reported", "announced", "launched", "raised", "policy", "market", "growth", "ai", "retail"] if term in lowered)
        score += min(5, _word_count(sentence) // 25)
        scored.append((score, index, sentence))

    selected = []
    total_words = 0
    for _, index, sentence in sorted(scored, key=lambda item: item[0], reverse=True):
        if index in {item[0] for item in selected}:
            continue
        selected.append((index, sentence))
        total_words += _word_count(sentence)
        if total_words >= TARGET_SUMMARY_WORDS:
            break

    selected.sort(key=lambda item: item[0])
    paragraph = " ".join(sentence for _, sentence in selected)
    return _clip(paragraph, 1000)


def _matched_text(item: dict, field: str) -> str:
    values = item.get(field) or []
    if isinstance(values, list):
        return "、".join(str(value) for value in values[:3])
    return str(values)


def fallback_summary(item: dict) -> dict:
    title = _clean_text(item.get("title", ""))
    source_text = _source_text(item)
    source = item.get("source_name", "公开来源")
    summary_zh = _summary_paragraph(title, source_text, source)
    business_dims = _matched_text(item, "matched_business_dimensions") or "核心业务"
    transfer_dims = _matched_text(item, "matched_transfer_dimensions") or "日常复盘"
    score = int(item.get("total_value_score", 0))
    noise_reason = item.get("noise_reason", "")

    why = "这条资讯值得关注，因为它连接了" + business_dims + "，可能影响渠道、产品、营销或流程判断。"
    implication = f"可作为 {business_dims} 方向的外部信号，用来校准品类机会、渠道动作或 AI 工作流优先级。"
    transfer = f"可迁移到 {transfer_dims}：提取其中的决策机制、用户行为变化或平台规则，而不是只记录事件本身。"
    action = "把这条新闻转成一个 10 分钟讨论点：它改变了哪个假设、影响哪个业务环节、是否值得连续观察。"

    if score < 55 and noise_reason:
        why = "这条资讯暂时只作为弱信号保留，主要原因是：" + noise_reason + "。"
        implication = "不建议直接据此决策，可放入观察池，等待更多高质量来源或同类案例验证。"
        action = "记录关键词和受影响平台，下次出现同类事件时再升级为趋势判断。"

    return {
        "one_sentence": _clip(summary_zh or title, 44),
        "summary": summary_zh,
        "summary_zh": summary_zh,
        "why_it_matters": _clip(why, 260),
        "business_implication": _clip(implication, 260),
        "knowledge_transfer": _clip(transfer, 260),
        "suggested_action": _clip(action, 220),
        "noise_reason": noise_reason,
    }


def _openai_payload(item: dict, model: str) -> dict:
    article_text = _source_text(item)
    source_data = {
        "title": item.get("title", ""),
        "rss_excerpt": _clip(_clean_text(item.get("summary_raw", "")), 500),
        "article_excerpt": _clip(article_text, MAX_ARTICLE_CHARS),
        "source_name": item.get("source_name", ""),
        "published_at": item.get("published_at", ""),
        "url": item.get("url", ""),
        "category": item.get("category", ""),
        "business_relevance_score": item.get("business_relevance_score", ""),
        "knowledge_transfer_score": item.get("knowledge_transfer_score", ""),
        "actionability_score": item.get("actionability_score", ""),
        "source_quality_score": item.get("source_quality_score", ""),
        "total_value_score": item.get("total_value_score", ""),
        "matched_business_dimensions": item.get("matched_business_dimensions", []),
        "matched_transfer_dimensions": item.get("matched_transfer_dimensions", []),
        "noise_reason": item.get("noise_reason", ""),
    }
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是面向跨境家具、ModernMate 品牌营销、品类规划和 AI 工作流的行业知识雷达分析师。"
                    "只基于用户给出的公开资讯字段输出判断，不要编造事实，不要泄露或假设内部信息。"
                    "核心任务不是复述新闻，而是筛选、判断和知识迁移。必须输出 JSON。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请为这条公开资讯生成以下字段："
                    "one_sentence(20-40字), summary_zh(80-160字中文摘要), why_it_matters(为什么重要), "
                    "business_implication(对跨境电商/家具家居/品牌营销/AI工作流的潜在影响), "
                    "knowledge_transfer(可迁移到品类规划、ModernMate、社媒、Hawkeye/Radar/Echo或组织流程的洞察), "
                    "suggested_action(一个可执行的小动作), noise_reason(如果分数低或噪音高，说明降权原因；否则可为空)。"
                    "不要复制标题当摘要；不要写泛泛的'值得关注'；如果证据不足，要明确谨慎。"
                    f"\n公开资讯字段：{json.dumps(source_data, ensure_ascii=False)}"
                ),
            },
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }


def ai_summary(item: dict) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=_openai_payload(item, model),
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        fallback = fallback_summary(item)
        return {
            "one_sentence": _clip(_clean_text(parsed.get("one_sentence", "")) or fallback["one_sentence"], 44),
            "summary": _clip(_clean_text(parsed.get("summary_zh", "")) or fallback["summary_zh"], 1000),
            "summary_zh": _clip(_clean_text(parsed.get("summary_zh", "")) or fallback["summary_zh"], 1000),
            "why_it_matters": _clip(_clean_text(parsed.get("why_it_matters", "")) or fallback["why_it_matters"], 320),
            "business_implication": _clip(_clean_text(parsed.get("business_implication", "")) or fallback["business_implication"], 320),
            "knowledge_transfer": _clip(_clean_text(parsed.get("knowledge_transfer", "")) or fallback["knowledge_transfer"], 320),
            "suggested_action": _clip(_clean_text(parsed.get("suggested_action", "")) or fallback["suggested_action"], 260),
            "noise_reason": _clip(_clean_text(parsed.get("noise_reason", "")) or item.get("noise_reason", ""), 260),
        }
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None


def summarize_item(item: dict) -> dict:
    summary = ai_summary(item) or fallback_summary(item)
    item.update(summary)
    return item
