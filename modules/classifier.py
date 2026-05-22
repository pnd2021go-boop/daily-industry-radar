from __future__ import annotations

from dataclasses import dataclass


CATEGORY_LABELS = {
    "cross_border_ecommerce": "跨境电商",
    "furniture_home": "家具与家居",
    "ai_tech": "AI 与科技",
    "consumer_retail": "科技与消费",
    "others": "其他观察",
}


KEYWORDS = {
    "cross_border_ecommerce": [
        "amazon", "tiktok shop", "temu", "shein", "shopify", "walmart marketplace",
        "wayfair marketplace", "ebay", "etsy", "cross-border", "seller", "marketplace",
        "跨境", "卖家", "电商", "平台政策",
    ],
    "furniture_home": [
        "wayfair", "ashley", "ikea", "furniture", "home", "interior", "mattress",
        "sofa", "retail furniture", "dtc furniture", "家居", "家具", "零售",
    ],
    "ai_tech": [
        "openai", "anthropic", "google ai", "perplexity", "ai search", "geo",
        "generative engine", "agent", "rag", "automation", "workflow", "人工智能",
        "大模型", "智能体", "自动化",
    ],
    "consumer_retail": [
        "consumer", "retail", "brand", "marketing", "gen z", "social media",
        "lifestyle", "electronics", "shopping", "消费", "品牌", "营销", "年轻人",
    ],
}


HIGH_SIGNAL_TERMS = [
    "launch", "policy", "regulation", "lawsuit", "earnings", "partnership", "tariff",
    "marketplace", "ai", "agent", "search", "retail", "trend", "报告", "政策", "发布",
    "合作", "监管", "关税", "平台",
]


@dataclass(frozen=True)
class Classification:
    category: str
    importance_score: int


def classify_item(title: str, summary: str = "", preferred_category: str | None = None) -> Classification:
    text = f"{title} {summary}".lower()
    scores = {category: 0 for category in KEYWORDS}
    for category, terms in KEYWORDS.items():
        scores[category] = sum(1 for term in terms if term.lower() in text)

    if preferred_category in scores:
        scores[preferred_category] += 2

    category = max(scores, key=scores.get)
    if scores[category] == 0:
        category = "others"

    signal_hits = sum(1 for term in HIGH_SIGNAL_TERMS if term.lower() in text)
    category_hits = scores.get(category, 0)
    importance = 1 + min(4, signal_hits + (1 if category_hits >= 2 else 0))
    return Classification(category=category, importance_score=importance)
