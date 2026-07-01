from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import re
from urllib.parse import urlparse


BUSINESS_TERMS = {
    "跨境电商": ["amazon", "shopify", "wayfair", "marketplace", "seller", "tiktok shop", "temu", "shein", "walmart", "ebay", "etsy", "cross-border", "ecommerce", "独立站", "跨境", "卖家"],
    "家具家居": ["furniture", "home", "interior", "sofa", "mattress", "ikea", "ashley", "wayfair", "home depot", "家居", "家具", "室内设计"],
    "AI工作流": ["ai agent", "agents", "agentic", "workflow", "automation", "rag", "openai", "anthropic", "gemini", "claude", "ai search", "智能体", "自动化"],
    "零售科技": ["retail media", "retail technology", "consumer behavior", "loyalty", "shopping", "store", "retail", "消费者", "零售"],
    "供应链": ["supply chain", "inventory", "logistics", "tariff", "warehouse", "fulfillment", "shipping", "库存", "物流", "关税", "供应链"],
    "品牌营销": ["brand", "marketing", "social media", "creator", "kol", "influencer", "content commerce", "campaign", "品牌", "营销", "社媒", "内容"],
}

TRANSFER_TERMS = {
    "品类规划": ["category", "assortment", "product", "launch", "trend", "consumer", "demand", "style", "品类", "产品", "趋势"],
    "产品机会识别": ["opportunity", "gap", "growth", "demand", "market", "new", "emerging", "增长", "机会"],
    "家具系列开发": ["furniture", "home", "interior", "sofa", "storage", "living room", "bedroom", "家居", "家具"],
    "ModernMate品牌营销": ["brand", "marketing", "creator", "social", "campaign", "loyalty", "retail media", "品牌", "营销"],
    "社媒内容策略": ["tiktok", "instagram", "social media", "creator", "short video", "content", "influencer", "社媒", "内容"],
    "AI工作流": ["agent", "workflow", "automation", "search", "assistant", "orchestration", "智能体", "自动化"],
    "组织流程优化": ["operation", "process", "planning", "collaboration", "productivity", "automation", "流程", "协作"],
    "中台方法论": ["platform", "infrastructure", "system", "data", "governance", "workflow", "中台", "平台"],
}

ACTION_TERMS = [
    "launch", "partnership", "pilot", "test", "experiment", "regulation", "policy", "lawsuit",
    "tariff", "inventory", "supply chain", "retail media", "agent", "automation", "consumer", "trend",
    "发布", "合作", "试点", "监管", "政策", "关税", "库存", "趋势",
]

HIGH_QUALITY_SOURCES = {
    "techcrunch", "the verge", "retail dive", "modern retail", "business of home",
    "furniture today", "home furnishings news", "shopify", "amazon", "openai", "anthropic",
    "google", "microsoft", "oracle", "mckinsey", "bain", "deloitte", "gartner",
    "reuters", "bloomberg", "wsj", "wall street journal", "cnbc", "homenewsnow",
}

LOW_QUALITY_SOURCES = {
    "openpr", "ein news", "streetinsider", "ad hoc news", "aol.com", "msn", "zawya",
    "simplywall", "tipranks", "stock titan", "mexc", "manila times", "newsfile",
}

NOISE_TERMS = [
    "stock", "shares", "price target", "investor update", "market size", "forecast", "cagr",
    "local store", "grand opening", "football team", "awards", "ranked", "watch brands",
]

THEME_DEFINITIONS = [
    {
        "key": "ai_agents",
        "name": "AI Agent 从助手变成业务执行单元",
        "terms": ["agent", "agentic", "workflow", "automation", "assistant", "orchestration", "ai supply chain", "voice ai"],
        "transfer": "Hawkeye / Radar / Echo 的任务编排、异常识别、自动跟进和复盘沉淀",
        "inspiration": "把 AI 从问答工具改造成可执行、可审计、可复盘的业务节点。",
        "action": "挑一个重复流程，定义输入、判断规则、输出字段和人工复核点，做一个一周小实验。",
    },
    {
        "key": "retail_discovery",
        "name": "零售发现链路正在被 AI 改写",
        "terms": ["ai search", "shopping app", "discovery", "consumer", "recommendation", "shopify", "search visibility"],
        "transfer": "ModernMate 独立站、Amazon/Wayfair listing、内容种草和站内搜索优化",
        "inspiration": "商品被发现的入口正在从关键词搜索转向 AI 推荐和上下文理解。",
        "action": "为一个核心 SKU 写出 AI 可理解的卖点结构：场景、痛点、尺寸、风格、搭配和证据。",
    },
    {
        "key": "furniture_channels",
        "name": "家具零售承压与渠道集中化",
        "terms": ["furniture", "home", "interior", "retailer", "store", "wayfair", "home depot", "ikea"],
        "transfer": "家具系列开发、价格带规划、渠道组合和线下/线上协同判断",
        "inspiration": "家具购买仍依赖信任、展示和服务，渠道变化会影响系列定位和内容表达。",
        "action": "把今日家具新闻拆成价格、渠道、场景、服务四个维度，检查现有产品线是否有空档。",
    },
    {
        "key": "retail_media",
        "name": "Retail Media 成为零售基础设施",
        "terms": ["retail media", "advertising", "loyalty", "customer data", "media offering"],
        "transfer": "Amazon / Walmart / Wayfair 广告投放、品牌内容资产和渠道 ROI 复盘",
        "inspiration": "零售平台正在把交易、会员、广告和数据打包成基础设施。",
        "action": "复盘一个渠道的内容资产是否能同时服务 SEO、广告、详情页和社媒投放。",
    },
    {
        "key": "platform_trust",
        "name": "内容治理成为平台信任机制",
        "terms": ["regulation", "policy", "compliance", "lawsuit", "fraud", "trust", "safety", "governance"],
        "transfer": "平台合规、评价治理、内容审核和跨境卖家风险预警",
        "inspiration": "平台增长越依赖第三方卖家和 AI 内容，治理能力越会成为竞争门槛。",
        "action": "建立一个平台政策观察清单：处罚原因、影响对象、触发信号、应对动作。",
    },
    {
        "key": "supply_chain_agents",
        "name": "供应链计划和库存管理开始 Agent 化",
        "terms": ["supply chain", "inventory", "planning", "logistics", "fulfillment", "warehouse", "tariff"],
        "transfer": "采购节奏、库存预警、补货判断、关税/物流风险监控",
        "inspiration": "供应链信息正在从报表监控转向自动判断和建议动作。",
        "action": "定义一个库存风险信号：销量、在途、毛利、交期、政策变化，先做人工版雷达。",
    },
    {
        "key": "content_commerce",
        "name": "DTC 品牌从产品故事转向渠道协同",
        "terms": ["dtc", "brand", "creator", "social", "content commerce", "influencer", "campaign", "tiktok"],
        "transfer": "ModernMate 品牌营销、社媒内容策略、KOL 合作和内容复用机制",
        "inspiration": "内容不只是曝光材料，而是连接发现、信任、转化和复购的渠道资产。",
        "action": "选一个产品卖点，改写成 3 条短视频脚本、1 条详情页模块和 1 条广告 hook。",
    },
]


@dataclass(frozen=True)
class RadarScores:
    business_relevance_score: int
    knowledge_transfer_score: int
    actionability_score: int
    source_quality_score: int
    total_value_score: int
    matched_business_dimensions: tuple[str, ...]
    matched_transfer_dimensions: tuple[str, ...]
    noise_reason: str


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def text_for_item(item: dict) -> str:
    return clean_text(" ".join([
        item.get("title", ""),
        item.get("summary_raw", ""),
        item.get("source_name", ""),
        item.get("category_hint", ""),
    ])).lower()


def _hit_dimensions(text: str, dimensions: dict[str, list[str]]) -> list[str]:
    hits = []
    for name, terms in dimensions.items():
        if any(term.lower() in text for term in terms):
            hits.append(name)
    return hits


def _score_from_hits(hit_count: int, strong_bonus: int = 0) -> int:
    return max(1, min(5, 1 + hit_count + strong_bonus))


def source_quality_score(item: dict) -> int:
    source = clean_text(item.get("source_name", "")).lower()
    host = urlparse(item.get("url", "")).netloc.lower().replace("www.", "")
    combined = f"{source} {host}"
    if any(name in combined for name in HIGH_QUALITY_SOURCES):
        return 5
    if any(name in combined for name in LOW_QUALITY_SOURCES):
        return 2
    if "google news" in source:
        return 3
    if host and not any(x in host for x in ["news.google", "msn", "aol"]):
        return 3
    return 2


def noise_reason_for(item: dict, text: str, business_hits: list[str], transfer_hits: list[str], source_score: int) -> str:
    reasons = []
    if not business_hits:
        reasons.append("与核心业务方向只有弱关键词关系")
    if not transfer_hits:
        reasons.append("暂时难以迁移到品类、营销或 AI 工作流")
    if source_score <= 2:
        reasons.append("来源质量或原创性偏弱")
    if any(term in text for term in NOISE_TERMS):
        reasons.append("更像泛财经、SEO 趋势稿或地方性新闻")
    return "；".join(reasons)


def score_item(item: dict) -> RadarScores:
    text = text_for_item(item)
    business_hits = _hit_dimensions(text, BUSINESS_TERMS)
    transfer_hits = _hit_dimensions(text, TRANSFER_TERMS)
    source_score = source_quality_score(item)
    action_hits = sum(1 for term in ACTION_TERMS if term.lower() in text)

    preferred_bonus = 1 if item.get("category_hint") in {
        "cross_border_ecommerce", "furniture_home", "ai_tech", "consumer_retail"
    } else 0
    business_score = _score_from_hits(len(business_hits), preferred_bonus)
    transfer_score = _score_from_hits(len(transfer_hits))
    action_score = max(1, min(5, 1 + min(4, action_hits // 2)))

    if any(term in text for term in NOISE_TERMS):
        action_score = max(1, action_score - 1)
        transfer_score = max(1, transfer_score - 1)

    total = round((
        business_score * 0.30
        + transfer_score * 0.25
        + action_score * 0.25
        + source_score * 0.20
    ) * 20)
    noise_reason = noise_reason_for(item, text, business_hits, transfer_hits, source_score)
    return RadarScores(
        business_relevance_score=business_score,
        knowledge_transfer_score=transfer_score,
        actionability_score=action_score,
        source_quality_score=source_score,
        total_value_score=total,
        matched_business_dimensions=tuple(business_hits),
        matched_transfer_dimensions=tuple(transfer_hits),
        noise_reason=noise_reason,
    )


def apply_radar_scores(item: dict) -> dict:
    scores = score_item(item)
    item.update({
        "business_relevance_score": scores.business_relevance_score,
        "knowledge_transfer_score": scores.knowledge_transfer_score,
        "actionability_score": scores.actionability_score,
        "source_quality_score": scores.source_quality_score,
        "total_value_score": scores.total_value_score,
        "matched_business_dimensions": list(scores.matched_business_dimensions),
        "matched_transfer_dimensions": list(scores.matched_transfer_dimensions),
        "noise_reason": scores.noise_reason,
    })
    return item


def assign_value_tiers(items: list[dict]) -> list[dict]:
    sorted_items = sorted(items, key=lambda item: (int(item.get("total_value_score", 0)), item.get("published_at", "")), reverse=True)
    caps = {"must_read": 3, "worth_scanning": 5, "weak_signals": 5}
    counts = Counter()
    for item in sorted_items:
        score = int(item.get("total_value_score", 0))
        if score >= 76 and counts["must_read"] < caps["must_read"]:
            tier = "must_read"
        elif score >= 62 and counts["worth_scanning"] < caps["worth_scanning"]:
            tier = "worth_scanning"
        elif score >= 48 and counts["weak_signals"] < caps["weak_signals"]:
            tier = "weak_signals"
        else:
            tier = "archive"
        item["value_tier"] = tier
        counts[tier] += 1
    return sorted_items


def tier_items(items: list[dict], tier: str) -> list[dict]:
    return [item for item in items if item.get("value_tier") == tier]


def _item_label(item: dict) -> str:
    return clean_text(item.get("title", "")) or "未命名资讯"


def _theme_matches(item: dict, terms: list[str]) -> bool:
    text = " ".join([
        text_for_item(item),
        clean_text(item.get("summary_zh", "")).lower(),
        clean_text(item.get("why_it_matters", "")).lower(),
    ])
    return any(term.lower() in text for term in terms)


def build_knowledge_transfer_cards(items: list[dict], max_cards: int = 5) -> list[dict]:
    priority_items = [item for item in items if item.get("value_tier") in {"must_read", "worth_scanning", "weak_signals"}]
    cards = []
    used_titles: set[str] = set()
    for theme in THEME_DEFINITIONS:
        matched = [item for item in priority_items if _theme_matches(item, theme["terms"])]
        if not matched:
            continue
        matched = sorted(matched, key=lambda item: int(item.get("total_value_score", 0)), reverse=True)[:3]
        titles = [_item_label(item) for item in matched]
        if all(title in used_titles for title in titles):
            continue
        used_titles.update(titles)
        cards.append({
            "theme_name": theme["name"],
            "what_happened": "；".join(item.get("one_sentence") or item.get("summary_zh") or _item_label(item) for item in matched[:2]),
            "why_important": theme["inspiration"],
            "transfer_to": theme["transfer"],
            "inspiration": f"可迁移到：{theme['transfer']}。关键不是复制新闻事件，而是提取其背后的流程、渠道或决策机制。",
            "small_action": theme["action"],
            "related_news": matched,
        })
        if len(cards) >= max_cards:
            break
    return cards


def build_weak_signal_notes(items: list[dict], max_notes: int = 5) -> list[dict]:
    signals = []
    for item in tier_items(items, "weak_signals")[:max_notes]:
        business_hits = item.get("matched_business_dimensions") or []
        signal = item.get("one_sentence") or item.get("title", "")
        observe = "关注后续是否出现同类平台动作、头部品牌跟进、政策变化或可量化业务影响。"
        if business_hits:
            observe = f"重点观察 {', '.join(business_hits[:2])} 方向是否出现连续案例或平台级变化。"
        signals.append({
            "signal": signal,
            "why_weak": item.get("noise_reason") or "当前只有单点新闻，尚不足以判断为稳定趋势。",
            "watch_next": observe,
            "item": item,
        })
    return signals


def build_executive_brief(items: list[dict], cards: list[dict]) -> dict:
    must = tier_items(items, "must_read")
    worth = tier_items(items, "worth_scanning")
    theme_names = [card["theme_name"] for card in cards[:3]]
    keywords = []
    for item in must + worth:
        keywords.extend(item.get("matched_business_dimensions") or [])
        keywords.extend(item.get("matched_transfer_dimensions") or [])
    keyword_counts = Counter(keywords)
    top_keywords = [name for name, _ in keyword_counts.most_common(6)] or ["AI工作流", "零售科技", "跨境电商"]

    if must:
        judgement = f"今天最值得关注的是：{must[0].get('one_sentence') or must[0].get('title', '')}"
    elif worth:
        judgement = f"今天没有绝对头部事件，但 {worth[0].get('one_sentence') or worth[0].get('title', '')} 值得快速扫一眼。"
    else:
        judgement = "今天信息噪音偏多，应优先保留观察，不急于形成业务判断。"

    sentences = []
    if theme_names:
        sentences.append(f"今天的结构性信号集中在{'、'.join(theme_names)}。")
    if must:
        sentences.append("必读内容优先指向可迁移的业务机制，而不是单条新闻本身。")
    if worth:
        sentences.append("值得快读的内容可用于补充渠道、平台政策、消费者行为和 AI 工作流的观察。")
    weak_count = len(tier_items(items, "weak_signals"))
    if weak_count:
        sentences.append(f"另有 {weak_count} 条弱信号适合放入连续观察池，等待更多案例验证。")
    sentences.append("今天的建议是少看泛资讯，多抓能转化为品类、营销或流程实验的信号。")

    return {
        "judgement": judgement,
        "keywords": top_keywords,
        "sentences": sentences[:5],
    }


def build_radar_context(items: list[dict]) -> dict:
    cards = build_knowledge_transfer_cards(items)
    return {
        "executive_brief": build_executive_brief(items, cards),
        "knowledge_cards": cards,
        "weak_signals": build_weak_signal_notes(items),
    }


def grouped_archive(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        grouped[item.get("category", "others")].append(item)
    for group in grouped.values():
        group.sort(key=lambda item: (int(item.get("total_value_score", 0)), item.get("published_at", "")), reverse=True)
    return dict(grouped)
