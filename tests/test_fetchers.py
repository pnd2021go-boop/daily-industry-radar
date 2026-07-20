from __future__ import annotations

import unittest

from modules.fetchers import _entry_to_item


class DiscoverySourceTests(unittest.TestCase):
    def test_bing_item_uses_original_url_and_publisher(self) -> None:
        entry = {
            "title": "Retailers add AI inventory planning",
            "summary": "Several US retailers are testing AI-assisted replenishment.",
            "link": "https://www.bing.com/news/apiclick.aspx?url=https%3A%2F%2Fwww.retaildive.com%2Fnews%2Fai-inventory%2F123",
        }
        item = _entry_to_item(entry, "Bing News: retail technology", "consumer_retail")
        self.assertEqual(item["url"], "https://www.retaildive.com/news/ai-inventory/123")
        self.assertEqual(item["source_name"], "Retail Dive")
        self.assertIn("AI-assisted", item["summary_raw"])

    def test_google_item_uses_embedded_publisher(self) -> None:
        entry = {
            "title": "Shopify launches new commerce tools - Reuters",
            "summary": "",
            "link": "https://news.google.com/rss/articles/example",
            "source": {"title": "Reuters", "href": "https://reuters.com"},
        }
        item = _entry_to_item(entry, "Google News: Shopify ecommerce", "cross_border_ecommerce")
        self.assertEqual(item["title"], "Shopify launches new commerce tools")
        self.assertEqual(item["source_name"], "Reuters")


if __name__ == "__main__":
    unittest.main()
