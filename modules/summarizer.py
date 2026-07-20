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


def source_context_profile(item: dict) -> tuple[int, str]:
    length = len(_source_text(item))
    if length >= 400:
        return 2, "正文充分"
    if length >= 100:
        return 1, "媒体摘要"
    return 0, "信息有限"


def hydrate_source_text(item: dict) -> dict:
    _source_text(item)
    score, label = source_context_profile(item)
    item["source_context_score"] = score
    item["source_context_label"] = label
    return item


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


def _fallback_action(item: dict) -> str:
    dimensions = set(item.get("matched_business_dimensions") or [])
    if "供应链" in dimensions:
        return "把事件涉及的政策、成本、交期和库存影响加入供应链观察表，并设定下一次复核时间。"
    if "家具家居" in dimensions:
        return "把新闻中的品类、价格带、渠道和消费场景拆成四列，与现有家具产品线做一次对照。"
    if "品牌营销" in dimensions or "零售科技" in dimensions:
        return "提取新闻中的用户触点和转化机制，形成一个可在 ModernMate 内容或投放中验证的小实验。"
    if "AI工作流" in dimensions:
        return "选取新闻中最具体的自动化场景，写出输入、判断、输出和人工复核点，评估是否纳入 Radar 或 Echo。"
    return "记录事件主体、变化、受影响环节和待验证假设，在周度复盘时检查是否出现第二个同类信号。"


def fallback_summary(item: dict) -> dict:
    title = _clean_text(item.get("title", ""))
    source_text = _source_text(item)
    source = item.get("source_name", "公开来源")
    summary_zh = _summary_paragraph(title, source_text, source)
    business_dims = _matched_text(item, "matched_business_dimensions") or "核心业务"
    transfer_dims = _matched_text(item, "matched_transfer_dimensions") or "日常复盘"
    score = int(item.get("total_value_score", 0))
    noise_reason = item.get("noise_reason", "")

    relevance = item.get("relevance_reason") or f"直接关联 {business_dims}。"
    why = relevance
    implication = f"该事件可用于校准 {business_dims} 的现有判断；在获得更多数据前，应把它视为外部证据而非确定结论。"
    transfer = f"可迁移到 {transfer_dims}，重点提取事件中的规则变化、用户行为、渠道机制或执行流程。"
    action = _fallback_action(item)

    if score < 55 and noise_reason:
        why = "这条资讯暂时只作为弱信号保留，主要原因是：" + noise_reason + "。"
        implication = "不建议直接据此决策，可放入观察池，等待更多高质量来源或同类案例验证。"
        action = "记录关键词和受影响平台，下次出现同类事件时再升级为趋势判断。"

    return {
        "one_sentence": _clip(title, 72),
        "summary": summary_zh,
        "summary_zh": summary_zh,
        "why_it_matters": _clip(why, 260),
        "business_implication": _clip(implication, 260),
        "knowledge_transfer": _clip(transfer, 260),
        "suggested_action": _clip(action, 220),
        "relevance_reason": relevance,
        "noise_reason": noise_reason,
    }


def _openai_payload(item: dict, model: str) -> dict:
    article_text = _source_text(item)
    source_data = {
        "title": item.get("title", ""),
        "rss_excerpt": _clip(_clean_text(item.get("summary_raw", "")), 500),
        "article_excerpt": _clip(article_text, MAX_ARTICLE_CHARS),
        "source_name": item.get("source_name", ""),
        "discovery_source": item.get("discovery_source", ""),
        "source_authority_label": item.get("source_authority_label", ""),
        "is_us_priority": item.get("is_us_priority", False),
        "source_context_label": item.get("source_context_label", ""),
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
        "relevance_reason": item.get("relevance_reason", ""),
        "noise_reason": item.get("noise_reason", ""),
    }
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是面向跨境家具、ModernMate 品牌营销、品类规划和 AI 工作流的行业情报编辑。"
                    "只基于给出的权威公开资讯输出，不要补写原文没有的事实、数字、因果或内部信息。"
                    "先让读者完整理解新闻事实，再解释业务相关性和行动含义。必须输出 JSON。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请为这条公开资讯生成以下字段："
                    "one_sentence(25-55字，写清核心事件), summary_zh(120-220字中文事实摘要), "
                    "relevance_reason(明确指出与哪些业务环节直接相关以及连接逻辑), why_it_matters(为什么重要), "
                    "business_implication(对跨境电商/家具家居/品牌营销/AI工作流的潜在影响), "
                    "knowledge_transfer(可迁移到品类规划、ModernMate、社媒、Hawkeye/Radar/Echo或组织流程的洞察), "
                    "suggested_action(一个可执行的小动作), noise_reason(如果分数低或噪音高，说明降权原因；否则可为空)。"
                    "summary_zh 必须先交代主体、动作、对象、时间或阶段、关键数字或范围、当前结果；"
                    "原文没有数字时不要虚构。摘要不得写业务建议，不得复制或只翻译标题。"
                    "relevance_reason 必须使用给出的匹配维度并解释连接，不要只写'与业务相关'。"
                    "why_it_matters 与 business_implication 不得重复；证据不足时明确写出尚不确定的部分。"
                    f"\n公开资讯字段：{json.dumps(source_data, ensure_ascii=False)}"
                ),
            },
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }


def ai_summary(item: dict) -> dict | None:
    openai_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    if openai_key:
        api_key = openai_key
        endpoint = "https://api.openai.com/v1/chat/completions"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif github_token:
        api_key = github_token
        endpoint = "https://models.github.ai/inference/chat/completions"
        model = os.getenv("GITHUB_MODELS_MODEL", "openai/gpt-4o")
    else:
        return None

    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
            json=_openai_payload(item, model),
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        fallback = fallback_summary(item)
        return {
            "one_sentence": _clip(_clean_text(parsed.get("one_sentence", "")) or fallback["one_sentence"], 72),
            "summary": _clip(_clean_text(parsed.get("summary_zh", "")) or fallback["summary_zh"], 1000),
            "summary_zh": _clip(_clean_text(parsed.get("summary_zh", "")) or fallback["summary_zh"], 1000),
            "why_it_matters": _clip(_clean_text(parsed.get("why_it_matters", "")) or fallback["why_it_matters"], 320),
            "business_implication": _clip(_clean_text(parsed.get("business_implication", "")) or fallback["business_implication"], 320),
            "knowledge_transfer": _clip(_clean_text(parsed.get("knowledge_transfer", "")) or fallback["knowledge_transfer"], 320),
            "suggested_action": _clip(_clean_text(parsed.get("suggested_action", "")) or fallback["suggested_action"], 260),
            "relevance_reason": _clip(_clean_text(parsed.get("relevance_reason", "")) or fallback["relevance_reason"], 260),
            "noise_reason": _clip(_clean_text(parsed.get("noise_reason", "")) or item.get("noise_reason", ""), 260),
        }
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None


def summarize_item(item: dict) -> dict:
    if "source_context_score" not in item:
        hydrate_source_text(item)
    generated = ai_summary(item)
    summary = generated or fallback_summary(item)
    item.update(summary)
    item["summary_generation_label"] = "AI 中文事实摘要" if generated else "原文事实摘录"
    summary_text = _clean_text(item.get("summary_zh") or item.get("summary", "")).lower()
    title = _clean_text(item.get("title", "")).lower()
    source = _clean_text(item.get("source_name", "")).lower()
    remainder = summary_text.replace(title, "").replace(source, "").strip(" .,:;|-–")
    item["summary_substantive"] = len(remainder) >= 60
    return item
