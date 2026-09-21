import re
from typing import Dict, Any, List, Optional
from app.rag import rag_pipeline
from app.tools import search_company_documents


class KnowledgeAgent:
    """
    Specialist Agent for company policy queries using 2-Stage RAG tools with metadata filtering.
    """
    AGENT_NAME = "KnowledgeAgent"
    TOOL_NAME = "RAG_Policy_Search"

    def __init__(self):
        self.rag = rag_pipeline

    def _infer_category(self, prompt: str) -> Optional[str]:
        prompt_lower = prompt.lower()
        matches = []
        if re.search(r'\bwfh\b|remote|work from home', prompt_lower):
            matches.append("wfh")
        if re.search(r'\bleave policy\b|annual leave|vacation policy|sick leave', prompt_lower):
            matches.append("leave")
        if re.search(r'\btravel\b|per diem|flight|hotel|reimbursement', prompt_lower):
            matches.append("travel")
        if re.search(r'\bsecurity\b|password|wifi|vpn|cybersecurity|\bit security\b', prompt_lower):
            matches.append("it_security")

        if len(matches) == 1:
            return matches[0]
        return None

    def process(
        self,
        prompt: str,
        category: Optional[str] = None,
        emp_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Processes a user query by querying the 2-Stage RAG pipeline.
        """
        if not category:
            category = self._infer_category(prompt)

        tool_res = search_company_documents(query=prompt, category=category, emp_id=emp_id, history=history)
        answer = tool_res["answer"]
        sources = tool_res["sources"]

        if "couldn't find information" in answer.lower():
            sources = []

        return {
            "answer": answer,
            "sources": sources,
            "tools_used": [self.TOOL_NAME],
            "agent_routed": self.AGENT_NAME
        }


knowledge_agent = KnowledgeAgent()
