import re
from typing import Dict, Any, List, Optional
from app.conversation import rewrite_followup
from app.rag import get_llm
from app.agents.knowledge_agent import knowledge_agent
from app.agents.hr_agent import hr_agent
from app.auth import Principal, enforce_prompt_scope
from app.security import detect_prompt_injection, normalize_input
from app.logging_config import logger


class OrchestratorRouter:
    """
    Orchestrator Router responsible for intent analysis and agent routing:
    - KnowledgeAgent (company policies / RAG queries)
    - HRAgent (employee info / leave requests)
    - Orchestrator_MultiAgent (hybrid queries)
    """

    def __init__(self):
        self.knowledge_agent = knowledge_agent
        self.hr_agent = hr_agent

    def route_and_execute(
        self,
        prompt: str,
        emp_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        principal: Optional[Principal] = None,
        actor_role: str = "EMPLOYEE",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines routing target, invokes agent(s), and returns consolidated response.
        Enforces security guardrails and prompt scope authorization post-rewriting.
        """
        # Step 1: Input Normalization & Prompt Injection Protection
        normalized_prompt = normalize_input(prompt)
        is_inj, pattern = detect_prompt_injection(normalized_prompt)
        if is_inj:
            logger.warning(f"[Security Guardrail] Prompt injection attempt blocked: pattern '{pattern}'")
            return {
                "answer": "I cannot fulfill this request because it violates safety guidelines.",
                "sources": [],
                "tools_used": [],
                "agent_routed": "Guardrail"
            }

        # Step 2: Conversational Follow-up Rewriting
        standalone = rewrite_followup(normalized_prompt, history, llm=get_llm())

        # Step 3: Post-rewriting Scope Authorization Check
        if principal:
            enforce_prompt_scope(standalone, principal)

        prompt_lower = standalone.lower()

        # Step 4: Intent Detection
        hr_keywords = [
            "leave", "leaves", "apply", "balance", "vacation", "profile",
            "employee", "my info", "who am i", "sick leave", "casual leave", "annual leave"
        ]
        prompt_has_emp_mention = bool(re.search(r'\bEMP\d{3}\b', standalone, re.IGNORECASE))
        is_hr_intent = prompt_has_emp_mention or any(re.search(r'\b' + re.escape(kw) + r'\b', prompt_lower) for kw in hr_keywords)

        knowledge_keywords = [
            "policy", "wfh", "work from home", "travel", "allowance", "per diem",
            "security", "password", "vpn", "mfa", "guidelines", "entitlement", "reimbursement", "rules"
        ]
        is_knowledge_intent = any(kw in prompt_lower for kw in knowledge_keywords)

        # Step 5: Route Execution
        if is_hr_intent and is_knowledge_intent:
            return self._execute_both(standalone, emp_id=emp_id, history=history, principal=principal, actor_role=actor_role, category=category)
        elif is_hr_intent:
            return self.hr_agent.process(standalone, emp_id=emp_id, history=history, principal=principal, actor_role=actor_role)
        elif is_knowledge_intent:
            return self.knowledge_agent.process(standalone, category=category, emp_id=emp_id, history=history)
        else:
            if "leave" in prompt_lower or "balance" in prompt_lower:
                return self.hr_agent.process(standalone, emp_id=emp_id, history=history, principal=principal, actor_role=actor_role)
            return self.knowledge_agent.process(standalone, category=category, emp_id=emp_id, history=history)

    def _execute_both(
        self,
        prompt: str,
        emp_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        principal: Optional[Principal] = None,
        actor_role: str = "EMPLOYEE",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Multi-Tool reasoning: Invokes KnowledgeAgent and HRAgent, then aggregates results."""
        knowledge_res = self.knowledge_agent.process(prompt, category=category, emp_id=emp_id, history=history)
        hr_res = self.hr_agent.process(prompt, emp_id=emp_id, history=history, principal=principal, actor_role=actor_role)

        answers = []
        if knowledge_res.get("answer"):
            answers.append(knowledge_res["answer"])
        if hr_res.get("answer"):
            answers.append(hr_res["answer"])

        combined_answer = "\n\n".join(answers)
        aggregated_sources = list(dict.fromkeys(knowledge_res.get("sources", []) + hr_res.get("sources", [])))
        aggregated_tools = list(dict.fromkeys(knowledge_res.get("tools_used", []) + hr_res.get("tools_used", [])))

        return {
            "answer": combined_answer,
            "sources": aggregated_sources,
            "tools_used": aggregated_tools,
            "agent_routed": "Orchestrator_MultiAgent"
        }


orchestrator = OrchestratorRouter()
