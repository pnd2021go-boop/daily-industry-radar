import json
import os
import unittest
from unittest.mock import Mock, patch

from modules.summarizer import ai_summary


class AiSummaryProviderTests(unittest.TestCase):
    def test_uses_github_models_when_openai_key_is_missing(self):
        item = {
            "title": "Retail AI changes product discovery",
            "article_text": "Retailers are testing AI shopping tools. " * 20,
            "source_name": "Reuters",
            "matched_business_dimensions": ["零售科技"],
            "matched_transfer_dimensions": ["ModernMate品牌营销"],
        }
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "summary_zh": "零售商正在测试新的人工智能购物工具，用于改变消费者发现和比较商品的方式。",
                "relevance_reason": "直接影响零售发现链路。",
            }, ensure_ascii=False)}}]
        }

        env = {"GITHUB_TOKEN": "workflow-token", "GITHUB_MODELS_MODEL": "openai/gpt-4o"}
        with patch.dict(os.environ, env, clear=True), patch("modules.summarizer.requests.post", return_value=response) as post:
            result = ai_summary(item)

        self.assertIn("人工智能购物工具", result["summary_zh"])
        self.assertEqual(post.call_args.args[0], "https://models.github.ai/inference/chat/completions")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "openai/gpt-4o")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer workflow-token")


if __name__ == "__main__":
    unittest.main()
