"""
Conversational context resolution for EmployeeMate.
Rewrites conversational follow-up questions into self-contained standalone questions using recent history.
"""
import re
from typing import List, Dict, Any, Optional
from app.security import sanitize_history
from app.logging_config import logger

MAX_TURNS = 6

_TOPIC_RE = re.compile(
    r"\bleaves?\b|\bleave balance\b|\bpto\b|\bvacation\b|\btime off\b|\bdays off\b|"
    r"\bwork from home\b|\bwfh\b|\bremote\b|\btravel\b|\bflight\b|\bhotel\b|"
    r"\breimburs\w*|\bexpenses?\b|\bpolicy\b|\bpolicies\b|\bbenefits?\b|"
    r"\bvpn\b|\bpassword\b|\blaptop\b|\bsecurity\b|\bholidays?\b|\bapply\b|\bEMP\d+\b",
    re.IGNORECASE,
)

_PROMPT = """You rewrite chat messages for an HR assistant.
Using the conversation history, rewrite the user's LATEST message as one
standalone message that makes sense without the history. Resolve pronouns,
omitted subjects, and references such as "it", "that", "them", "next month",
"after applying". Keep employee IDs, numbers and dates exactly as written.
Do NOT answer the message. If it is already standalone, return it unchanged.
Output only the rewritten message.

Conversation history:
{history}

Latest message: {message}
Rewritten message:"""


_REFERENTIAL_RE = re.compile(
    r"\b(it|that|them|those|this|these|its|their)\b|"
    r"\b(next month|next week|next year|after that|after applying|instead|then|again|later|before that|prior to that)\b|"
    r"\b(what about|how about|what of|how many|how much|do i have left|can i take|could i|what if|how so|why|how come|tell me more|anything else)\b|"
    r"^(and|or|so|also|after|for|in|on|with|during|before|by|from|to|at)\b|"
    r"\b(left|remaining|other|another|same|previous|former|latter|more|details?)\b",
    re.IGNORECASE,
)


def _is_referential(message: str) -> bool:
    """Check if message contains referential pronouns, time shifts, or follow-up signals."""
    if _REFERENTIAL_RE.search(message):
        return True
    words = message.strip().split()
    if len(words) < 6:
        first_word = words[0].lower().strip("?,.!")
        if first_word in {"why", "how", "when", "where", "who", "which", "can", "could", "would", "should", "is", "are", "do", "does", "any"}:
            if len(words) <= 3:
                return True
    return False


def _format(history: List[Dict[str, str]]) -> str:
    return "\n".join(f"{h['role'].capitalize()}: {h['content']}" for h in history)


def _rule_based(message: str, history: List[Dict[str, str]]) -> str:
    """Fallback when no LLM is available: borrow the topic from recent user turns only if referential signal is present."""
    if _TOPIC_RE.search(message) or not _is_referential(message):
        return message
    for turn in reversed(history):
        if turn.get("role") == "user" and _TOPIC_RE.search(turn.get("content", "")):
            return f"{message} (Context: the user's earlier question was: \"{turn['content']}\")"
    return message


def rewrite_followup(
    message: str,
    history: Optional[List[Dict[str, Any]]] = None,
    llm: Optional[Any] = None
) -> str:
    """
    Returns a standalone version of `message`. Never raises an exception.
    Applies security sanitization to history prior to rewriting.
    """
    if not message or not message.strip():
        return message

    clean_history = sanitize_history(history or [])
    if not clean_history:
        return message

    if llm is not None:
        try:
            formatted_hist = _format(clean_history)
            prompt_str = _PROMPT.format(history=formatted_hist, message=message)
            
            # Call LLM invoke safely
            reply = None
            if hasattr(llm, "invoke"):
                reply = llm.invoke([
                    {"role": "system", "content": "You rewrite conversational follow-up messages into standalone queries."},
                    {"role": "user", "content": prompt_str}
                ])
            
            from app.rag import extract_text_from_response
            text = extract_text_from_response(reply)
            
            # Guard against empty or runaway output
            if text and len(text) <= 3 * len(message) + 200:
                return text
            else:
                logger.warning("[Rewrite Followup] LLM output exceeded length guard, falling back to rule-based rewrite.")
        except Exception as e:
            logger.debug(f"[Rewrite Followup Error] {e}")

    return _rule_based(message, clean_history)