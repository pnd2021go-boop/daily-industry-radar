from __future__ import annotations

import json
import os
import re
from html import unescape

import requests
from bs4 import BeautifulSoup


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


def _summary_paragraph(title: str, raw: str, source: str) -> str:
    if raw:
        return _clip(
            f"{source} 的公开资讯显示，{raw} 这条消息与“{title}”相关，"
            "可用于了解相关平台、品牌、技术或消费市场的最新公开动态。具体细节仍应以原文链接为准。",
            260,
        )
    return _clip(
        f"{source} 发布了题为“{title}”的公开资讯。由于当前 RSS 未提供更完整正文，"
        "本摘要仅依据标题、来源和发布时间进行中性整理，主要用于提示该领域出现了新的公开动态；"
        "具体事件背景、数据口径和影响范围仍需打开原文进一步核对。",
        260,
    )


def fallback_summary(item: dict) -> dict:
    title = _clean_text(item.get("title", ""))
    raw = _clean_text(item.get("summary_raw", ""))
    source = item.get("source_name", "公开来源")
    basis = raw or title
    return {
        "one_sentence": _clip(basis, 40),
        "summary": _summary_paragraph(title, raw, source),
        "why_it_matters": "",
    }


def _openai_payload(item: dict, model: str) -> dict:
    source_data = {
        "title": item.get("title", ""),
        "rss_excerpt": _clip(_clean_text(item.get("summary_raw", "")), 500),
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
                    "请生成 one_sentence(20-40字) 和 summary(120-220字，完整一段话)。"
                    "summary 只能基于给定字段，不确定处要谨慎表达，不能扩写为未经证实的事实。"
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
            "summary": _clip(_clean_text(parsed.get("summary", "")), 260),
            "why_it_matters": "",
        }
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None


def summarize_item(item: dict) -> dict:
    summary = ai_summary(item) or fallback_summary(item)
    item.update(summary)
    return item
