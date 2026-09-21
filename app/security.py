import re
import unicodedata
from typing import List, Dict, Any, Tuple
from app.logging_config import logger

MAX_PROMPT_LENGTH = 2000
CANARY_TOKEN = "CANARY_PROTECT_SECRET_TOKEN_9981"

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|system)\s+instructions",
    r"system\s+prompt\s+override",
    r"you\s+are\s+now\s+(in\s+)?dan\s+mode",
    r"disregard\s+all\s+previous\s+directives",
    r"bypass\s+safety\s+guidelines",
    r"reveal\s+secret\s+key",
    r"print\s+system\s+prompt",
    r"forget\s+all\s+rules",
    r"override\s+instructions",
    r"jailbreak",
]


def normalize_input(text: str) -> str:
    """
    Normalizes unicode characters (NFKC) and strips zero-width and invisible control characters.
    """
    if not text:
        return ""
    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)
    # Strip zero-width spaces and control characters (except standard newlines/tabs)
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF\x00-\x08\x0B\x0C\x0E-\x1F]', '', normalized)
    return cleaned.strip()


def detect_prompt_injection(prompt: str) -> Tuple[bool, str]:
    """
    Checks if a prompt contains malicious prompt injection patterns.
    Returns (is_injection: bool, pattern_matched: str).
    """
    normalized_prompt = normalize_input(prompt)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized_prompt, re.IGNORECASE):
            return True, pattern
    return False, ""


def sanitize_history(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Sanitizes conversation history:
    1. Forces roles to 'user' or 'assistant' only.
    2. Drops turns containing prompt injection attacks.
    3. Truncates individual turn content to 1000 characters.
    """
    sanitized: List[Dict[str, str]] = []
    if not history:
        return sanitized

    for turn in history:
        if not isinstance(turn, dict):
            continue

        raw_role = (turn.get("role") or turn.get("sender") or "user").lower().strip()
        role = "assistant" if raw_role in ["assistant", "bot"] else "user"

        content = normalize_input(str(turn.get("content") or turn.get("text") or ""))
        if not content:
            continue

        # Drop turns that contain prompt injections
        is_inj, _ = detect_prompt_injection(content)
        if is_inj:
            logger.warning("[Security Guardrail] Dropped prompt injection attempt inside conversation history turn.")
            continue

        # Truncate turn length
        if len(content) > 1000:
            content = content[:1000]

        sanitized.append({"role": role, "content": content})

    return sanitized[-6:]  # Keep last 6 clean turns


def wrap_context(matching_docs: List[Any]) -> str:
    """
    Wraps retrieved document chunks inside explicit XML <document> tags to establish clear data boundaries.
    """
    doc_blocks = []
    for i, doc in enumerate(matching_docs, 1):
        source = getattr(doc, "metadata", {}).get("source") or getattr(doc, "metadata", {}).get("file_name") or "document"
        content = getattr(doc, "page_content", str(doc))
        doc_blocks.append(f'<document id="{i}" source="{source}">\n{content}\n</document>')
    return "\n\n".join(doc_blocks)


def verify_canary(response_text: str) -> str:
    """
    Checks if the LLM output leaked the canary token. If leaked, redacts it.
    """
    if CANARY_TOKEN in response_text:
        logger.error("[Security Warning] Canary token leaked in LLM output! Redacting output.")
        return "I am sorry, but I cannot fulfill this request due to security policies."
    return response_text
