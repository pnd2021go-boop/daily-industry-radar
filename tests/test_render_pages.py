from __future__ import annotations

import unittest

from modules.render_pages import render_daily_page


def sample_item() -> dict:
    return {
        "title": "Amazon expands AI inventory planning for US sellers",
        "summary_zh": "Amazon 扩大面向美国卖家的 AI 库存计划工具，覆盖补货判断与异常提醒；当前仍处于分阶段推广，公开信息尚未说明全部卖家范围。",
        "relevance_reason": "直接关联 跨境电商、供应链、AI工作流；可迁移到 品类规划、组织流程优化。",
        "why_it_matters": "平台正在把库存判断从报表查看推进到自动建议。",
        "business_implication": "卖家的补货节奏、库存风险识别和运营分工可能随之变化。",
        "knowledge_transfer": "可用于 Radar 的库存异常识别与人工复核设计。",
        "suggested_action": "选择一个 SKU 建立人工版异常判断表。",
        "source_name": "Reuters",
        "source_authority_label": "美国权威/官方",
        "is_us_priority": True,
        "is_authoritative_source": True,
        "source_context_label": "正文充分",
        "published_at": "2026-07-20T00:00:00+00:00",
        "url": "https://reuters.com/example",
        "category": "cross_border_ecommerce",
        "value_tier": "must_read",
        "business_relevance_score": 5,
        "knowledge_transfer_score": 5,
        "actionability_score": 4,
        "source_quality_score": 5,
        "total_value_score": 94,
    }


class RenderPageTests(unittest.TestCase):
    def test_page_has_interactive_processing_tools(self) -> None:
        item = sample_item()
        html = render_daily_page([item], "2026-07-20", "Daily Industry Radar", radar_context={})
        self.assertIn('id="radar-search"', html)
        self.assertIn("data-save", html)
        self.assertIn("data-share", html)
        self.assertIn('id="saved-dialog"', html)
        self.assertIn("navigator.share", html)
        self.assertIn("localStorage", html)

    def test_page_leads_with_facts_and_relevance(self) -> None:
        item = sample_item()
        html = render_daily_page([item], "2026-07-20", "Daily Industry Radar", radar_context={})
        self.assertIn(item["summary_zh"], html)
        self.assertIn(item["relevance_reason"], html)
        self.assertIn("美国优先", html)
        self.assertNotIn("—", html)


if __name__ == "__main__":
    unittest.main()
