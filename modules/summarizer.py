from __future__ import annotations

import json
import os
import re
from html import unescape

import requests
from bs4 import BeautifulSoup


ARTICLE_TIMEOUT_SECONDS = 8
MAX_ARTICLE_CHARS = 6000
MIN_SOURCE_CHARS = 280


def _clean_text(text: str) -> str:
    raw = unescape(text or "")
    if "<" in raw and ">" in raw:
        soup = BeautifulSoup(raw, "html.parser")
        raw = soup.get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", raw).strip()
    return cleaned


def _clip(text: str, limit: int) -> str:
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
    article_text = item.get("article_text") or _article_text_from_url(item.get("url", ""))
    item["article_text"] = article_text
    raw = _clean_text(item.get("summary_raw", ""))
    return article_text or raw


def has_enough_source_text(item: dict) -> bool:
    return len(_source_text(item)) >= MIN_SOURCE_CHARS


def _summary_paragraph(title: str, text: str, source: str) -> str:
    if not text:
        return f"{source} 发布了题为“{title}”的公开资讯，但当前信息源没有提供足够正文内容。请打开原文链接查看完整报道。"

    sentences = re.split(r"(?<=[。！？.!?])\s+", text)
    useful = []
    for sentence in sentences:
        cleaned = _clean_text(sentence)
        if len(cleaned) >= 30:
            useful.append(cleaned)
        if len(" ".join(useful)) >= 900:
            break
    paragraph = " ".join(useful) if useful else text
    return _clip(paragraph, 1400)

def fallback_summary(item: dict) -> dict:
    title = _clean_text(item.get("title", ""))
    source_text = _source_text(item)
    source = item.get("source_name", "公开来源")
    basis = source_text or title
    return {
        "one_sentence": _clip(basis, 40),
        "summary": _summary_paragraph(title, source_text, source),
        "why_it_matters": "",
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
    }
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是公开新闻摘要助手。只基于用户给出的标题、来源、发布时间和链接写中性摘要。"
                    "不要编造事实，不要写内部策略、内部判断或敏感建议。输出 JSON。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请生成 one_sentence(20-40字) 和 summary。summary 必须是一整段完整中文，"
                    "约等于 180-220 个英文单词的信息量，概括新闻报道核心内容：谁、发生了什么、"
                    "关键背景、主要数据或变化、报道中明确提到的影响。不要写“可用于了解”“请以原文为准”"
                    "这类模板废话。summary 只能基于给定字段，不确定处要谨慎表达，不能扩写为未经证实的事实。"
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
        return {
            "one_sentence": _clip(_clean_text(parsed.get("one_sentence", "")), 40),
            "summary": _clip(_clean_text(parsed.get("summary", "")), 1600),
            "why_it_matters": "",
        }
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None


def summarize_item(item: dict) -> dict:
    summary = ai_summary(item) or fallback_summary(item)
    item.update(summary)
    return item
