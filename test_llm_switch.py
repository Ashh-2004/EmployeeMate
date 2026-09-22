"""
Unit tests for LLM Provider Switch, Retry Helper, Followup Query Rewriting, and Leave Details Extraction.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.rag import get_llm, invoke_llm_with_retry, rewrite_followup, rag_pipeline
from app.agents.hr_agent import extract_leave_details
from app.agents.orchestrator import orchestrator


class TestLLMProviderSwitch(unittest.TestCase):

    def test_01_get_llm_returns_none_when_keys_missing(self):
        """Test get_llm returns None when API keys are empty for gemini/openai"""
        with patch.object(settings, "llm_provider", "gemini"), \
             patch.object(settings, "google_api_key", ""), \
             patch.object(settings, "openai_api_key", ""):
            llm = get_llm()
            self.assertIsNone(llm)

    def test_01b_get_llm_ollama_provider(self):
        """Test get_llm returns ChatOpenAI instance with Ollama configuration"""
        with patch.object(settings, "llm_provider", "ollama"):
            with patch("langchain_openai.ChatOpenAI") as mock_ollama:
                mock_ollama.return_value = "MockOllamaInstance"
                llm = get_llm()
                self.assertEqual(llm, "MockOllamaInstance")

    def test_02_get_llm_gemini_provider(self):
        """Test get_llm returns ChatGoogleGenerativeAI instance for gemini provider"""
        with patch.object(settings, "llm_provider", "gemini"), \
             patch.object(settings, "google_api_key", "test_google_key"):
            with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_gemini:
                mock_gemini.return_value = "MockGeminiInstance"
                llm = get_llm()
                self.assertEqual(llm, "MockGeminiInstance")
                mock_gemini.assert_called_once_with(
                    model=settings.gemini_model,
                    google_api_key="test_google_key",
                    temperature=0.0,
                    request_timeout=getattr(settings, "llm_timeout", 60.0),
                    max_retries=0
                )

    def test_03_get_llm_openai_provider(self):
        """Test get_llm returns ChatOpenAI instance for openai provider"""
        with patch.object(settings, "llm_provider", "openai"), \
             patch.object(settings, "openai_api_key", "test_openai_key"):
            with patch("langchain_openai.ChatOpenAI") as mock_openai:
                mock_openai.return_value = "MockOpenAIInstance"
                llm = get_llm()
                self.assertEqual(llm, "MockOpenAIInstance")

    def test_04_invoke_llm_with_retry_rate_limit(self):
        """Test invoke_llm_with_retry retries twice on 429 rate limit error before returning None"""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("HTTP 429 Too Many Requests: quota exceeded")

        with patch("time.sleep") as mock_sleep:
            res = invoke_llm_with_retry(mock_llm, [{"role": "user", "content": "Hello"}])
            self.assertIsNone(res)
            # Should attempt 3 times (initial + 2 retries)
            self.assertEqual(mock_llm.invoke.call_count, 3)
            # Should sleep 2s then 5s
            self.assertEqual(mock_sleep.call_args_list, [unittest.mock.call(2), unittest.mock.call(5)])

    def test_05_rewrite_followup_with_history(self):
        """Test rewrite_followup resolves context using LLM"""
        mock_response = MagicMock()
        mock_response.content = "What is the leave policy for EMP001?"

        history = [
            {"role": "user", "content": "I am EMP001."},
            {"role": "assistant", "content": "Hello EMP001! How can I help you today?"}
        ]

        with patch("app.rag.get_llm") as mock_get_llm, \
             patch("app.rag.invoke_llm_with_retry", return_value=mock_response):
            mock_get_llm.return_value = MagicMock()
            rewritten = rewrite_followup("What is the leave policy?", history)
            self.assertIn("leave policy", rewritten.lower())

    def test_06_rewrite_followup_fallback_when_llm_unavailable(self):
        """Test rewrite_followup returns original message when LLM is unavailable"""
        with patch("app.rag.get_llm", return_value=None):
            history = [{"role": "user", "content": "Hello"}]
            original = "How many leaves do I have?"
            result = rewrite_followup(original, history)
            self.assertEqual(result, original)

    def test_07_extract_leave_dates_valid(self):
        """Test extract_leave_dates parses date string and returns (start, end, days)"""
        from app.leave_dates import extract_leave_dates
        from datetime import date
        start, end, days = extract_leave_dates("Apply leave for EMP001 from 20 September to 22 September", date(2026, 9, 20))
        self.assertEqual(start, date(2026, 9, 20))
        self.assertEqual(end, date(2026, 9, 22))
        self.assertEqual(days, 3)

    def test_08_extract_leave_dates_rejection(self):
        """Test extract_leave_dates raises ValueError on invalid dates or missing dates"""
        from app.leave_dates import extract_leave_dates
        from datetime import date
        with self.assertRaises(ValueError):
            extract_leave_dates("Apply leave tomorrow", date(2026, 9, 20))

    def test_10_extract_leave_dates_sept_abbreviation(self):
        """Test extract_leave_dates correctly handles '20 Sept to 22 Sept' (3 days)"""
        from app.leave_dates import extract_leave_dates
        from app.mock_db import MockDatabase
        from datetime import date
        s_date, e_date, days = extract_leave_dates("Apply leave for EMP001 from 20 Sept to 22 Sept", date(2026, 9, 20))
        self.assertEqual(s_date, date(2026, 9, 20))
        self.assertEqual(e_date, date(2026, 9, 22))
        self.assertEqual(days, 3)

        orchestrator.hr_agent.db = MockDatabase()
        res = orchestrator.route_and_execute("Apply leave for EMP001 from 20 Sept to 22 Sept")
        self.assertIn("3 day(s)", res["answer"])
        self.assertIn("2026-09-20 to 2026-09-22", res["answer"])


if __name__ == "__main__":
    unittest.main()
