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


def fallback_summary(item: dict) -> dict:
    title = _clean_text(item.get("title", ""))
    raw = _clean_text(item.get("summary_raw", ""))
    source = item.get("source_name", "公开来源")
    basis = raw or title
    return {
        "one_sentence": _clip(basis, 40),
        "summary": _clip(basis if raw else f"{source} 发布相关公开资讯：{title}", 150),
        "why_it_matters": "该资讯反映相关行业的公开动态，可作为观察平台政策、市场变化或技术趋势的参考。",
    }


def _openai_payload(item: dict, model: str) -> dict:
    source_data = {
        "title": item.get("title", ""),
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
                    "请生成 one_sentence(20-40字)、summary(80-150字)、why_it_matters(中性表达)。"
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
            "summary": _clip(_clean_text(parsed.get("summary", "")), 150),
            "why_it_matters": _clip(_clean_text(parsed.get("why_it_matters", "")), 120),
        }
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None


def summarize_item(item: dict) -> dict:
    summary = ai_summary(item) or fallback_summary(item)
    item.update(summary)
    return item
