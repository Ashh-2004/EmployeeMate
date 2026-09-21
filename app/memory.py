import threading
from collections import deque
from typing import List, Dict, Any, Optional
from app.logging_config import logger


class ConversationMemory:
    """
    Thread-safe, bounded in-memory store for user conversation histories.
    Keyed by f"{emp_id}:{session_id}".
    Maintains up to 6 turns (3 exchanges) per session, with max 100 sessions total.
    """

    def __init__(self, max_turns: int = 6, max_sessions: int = 100):
        self._lock = threading.Lock()
        self._max_turns = max_turns
        self._max_sessions = max_sessions
        # Stores dict of key -> deque of turn dicts
        self._sessions: Dict[str, deque] = {}

    def _make_key(self, emp_id: Optional[str], session_id: Optional[str]) -> str:
        clean_emp = (emp_id or "ANONYMOUS").strip().upper()
        clean_session = (session_id or "DEFAULT").strip()
        return f"{clean_emp}:{clean_session}"

    def add_turn(self, emp_id: Optional[str], session_id: Optional[str], role: str, content: str) -> None:
        """Adds a single conversation turn to memory."""
        if not content:
            return

        key = self._make_key(emp_id, session_id)
        with self._lock:
            if key not in self._sessions:
                # Evict oldest session if maximum sessions limit reached
                if len(self._sessions) >= self._max_sessions:
                    oldest_key = next(iter(self._sessions))
                    del self._sessions[oldest_key]
                    logger.debug(f"[Memory] Evicted oldest conversation session: {oldest_key}")
                self._sessions[key] = deque(maxlen=self._max_turns)

            self._sessions[key].append({
                "role": role.strip().lower(),
                "content": content.strip()
            })

    def get_history(self, emp_id: Optional[str], session_id: Optional[str]) -> List[Dict[str, str]]:
        """Retrieves recent conversation history for a given session."""
        key = self._make_key(emp_id, session_id)
        with self._lock:
            if key in self._sessions:
                return list(self._sessions[key])
            return []

    def clear(self, emp_id: Optional[str], session_id: Optional[str]) -> None:
        """Clears memory for a given session."""
        key = self._make_key(emp_id, session_id)
        with self._lock:
            if key in self._sessions:
                del self._sessions[key]


# Singleton instance of server-side memory
memory_store = ConversationMemory()
