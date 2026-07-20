import tempfile
import unittest
from pathlib import Path

from modules.archive import append_news_archive, load_news_archive


class ArchiveFallbackTests(unittest.TestCase):
    def test_loads_only_same_day_snapshot_with_types_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.csv"
            append_news_archive([{
                "title": "Retail signal",
                "url": "https://example.com/signal",
                "summary_zh": "中文事实摘要",
                "total_value_score": 72,
                "is_us_priority": True,
                "summary_substantive": True,
            }], "2026-07-20", path)

            items = load_news_archive(path, "2026-07-20")
            prior = load_news_archive(path, "2026-07-19")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["total_value_score"], 72)
        self.assertTrue(items[0]["is_us_priority"])
        self.assertEqual(items[0]["summary"], "中文事实摘要")
        self.assertEqual(prior, [])


if __name__ == "__main__":
    unittest.main()
