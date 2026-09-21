import sys
import os
from unittest.mock import MagicMock

# Force environment variables BEFORE importing any app modules
os.environ["LLM_PROVIDER"] = "none"
os.environ["JWT_SECRET"] = "test-secret-key-12345"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"
os.environ["DEMO_EMPLOYEE_PASSWORD"] = "emp123"
os.environ["DEMO_HR_PASSWORD"] = "hr123"
os.environ["MAX_VECTOR_DISTANCE"] = "1.35"
os.environ["MIN_RERANK_SCORE"] = "0.0"
os.environ["LOG_LEVEL"] = "WARNING"

# Block sentence_transformers to force DeterministicHashEmbeddings fallback in test environment
sys.modules["sentence_transformers"] = None
