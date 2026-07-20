from __future__ import annotations

import unittest

from modules.insights import apply_radar_scores, assign_value_tiers, build_knowledge_transfer_cards, source_profile


class SourceProfileTests(unittest.TestCase):
    def test_us_authority_is_prioritized(self) -> None:
        profile = source_profile({"source_name": "Reuters", "url": "https://reuters.com/article"})
        self.assertEqual(profile["score"], 5)
        self.assertTrue(profile["is_us_priority"])
        self.assertTrue(profile["is_authoritative"])

    def test_us_trade_media_is_authoritative(self) -> None:
        profile = source_profile({"source_name": "Retail Dive", "url": "https://retaildive.com/news/x"})
        self.assertEqual(profile["score"], 4)
        self.assertTrue(profile["is_us_priority"])
        self.assertTrue(profile["is_authoritative"])

    def test_low_quality_source_is_rejected(self) -> None:
        profile = source_profile({"source_name": "openPR", "url": "https://openpr.com/news/x"})
        self.assertEqual(profile["score"], 1)
        self.assertFalse(profile["is_authoritative"])

    def test_similar_publisher_name_does_not_inherit_authority(self) -> None:
        self.assertFalse(source_profile({"source_name": "Startup Fortune", "url": "https://news.google.com/x"})["is_authoritative"])
        self.assertFalse(source_profile({"source_name": "The Sunday Guardian", "url": "https://news.google.com/x"})["is_authoritative"])

    def test_authority_domain_and_press_release_path(self) -> None:
        self.assertTrue(source_profile({"source_name": "reuters.com", "url": "https://www.reuters.com/business/story"})["is_authoritative"])
        self.assertFalse(source_profile({"source_name": "Fortune", "url": "https://fortune.com/press-release/example"})["is_authoritative"])

    def test_google_query_does_not_impersonate_official_source(self) -> None:
        profile = source_profile({
            "source_name": "Unknown Local Blog",
            "discovery_source": "Google News: Amazon marketplace policy",
            "url": "https://news.google.com/rss/articles/x",
        })
        self.assertFalse(profile["is_authoritative"])

    def test_relevance_reason_and_tier_require_authority(self) -> None:
        item = {
            "title": "Amazon tests AI inventory agents for marketplace sellers",
            "summary_raw": "The pilot automates inventory planning and seller workflows.",
            "source_name": "Unknown Local Blog",
            "url": "https://example.com/story",
            "category_hint": "cross_border_ecommerce",
            "published_at": "2026-07-20T00:00:00+00:00",
        }
        apply_radar_scores(item)
        item["total_value_score"] = 99
        assigned = assign_value_tiers([item])
        self.assertEqual(assigned[0]["value_tier"], "archive")
        self.assertIn("直接关联", assigned[0]["relevance_reason"])

    def test_priority_tier_requires_source_context(self) -> None:
        item = {
            "title": "Shopify launches new inventory workflow for US merchants",
            "summary_raw": "Shopify announced an inventory workflow for merchants using multiple fulfillment locations.",
            "source_name": "Shopify",
            "url": "https://shopify.com/news/inventory-workflow",
            "category_hint": "cross_border_ecommerce",
            "published_at": "2026-07-20T00:00:00+00:00",
        }
        apply_radar_scores(item)
        item.update({"total_value_score": 90, "actionability_score": 4, "source_context_score": 0, "summary_substantive": True})
        self.assertEqual(assign_value_tiers([item])[0]["value_tier"], "archive")
        item["source_context_score"] = 2
        self.assertEqual(assign_value_tiers([item])[0]["value_tier"], "must_read")

    def test_non_furniture_commerce_story_does_not_create_furniture_theme(self) -> None:
        item = {
            "title": "Ecommerce subscription management software for DTC brands",
            "summary_raw": "A guide to recurring billing and customer retention for online brands.",
            "source_name": "Shopify",
            "category": "cross_border_ecommerce",
            "value_tier": "worth_scanning",
            "total_value_score": 70,
            "summary_zh": "订阅管理工具帮助 DTC 品牌处理周期计费与客户留存。",
            "why_it_matters": "直接关联跨境电商。",
        }
        cards = build_knowledge_transfer_cards([item])
        self.assertNotIn("家具零售承压与渠道集中化", [card["theme_name"] for card in cards])


if __name__ == "__main__":
    unittest.main()
