import re
from typing import Dict, Any, List, Optional
from app.mock_db import db
from app.tools import apply_leave_with_rbac
from app.leave_dates import extract_leave_dates
from app.rag import get_llm, invoke_llm_with_retry, extract_text_from_response
from app.auth import Principal, authorize_target
from app.logging_config import logger
from app.security import sanitize_history


def is_leave_application_request(prompt: str) -> bool:
    prompt_lower = prompt.lower()

    has_action = bool(re.search(
        r"\b(apply|submit|request|book)\b", prompt_lower
    ))

    has_leave_term = bool(re.search(
        r"\b(leave|leaves|vacation|time off|days off)\b", prompt_lower
    ))

    return has_action and has_leave_term


def extract_leave_details(message: str, today: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Backward-compatible helper using extract_leave_dates."""
    try:
        s_dt, e_dt, calc_days = extract_leave_dates(message)
        return {
            "start_date": s_dt.strftime("%Y-%m-%d"),
            "end_date": e_dt.strftime("%Y-%m-%d"),
            "reason": "Personal",
            "calc_days": calc_days
        }
    except Exception:
        return None


class HRAgent:
    """
    Persona: HR Assistant for EmployeeMate.
    Executes employee info retrieval and leave application with strict RBAC enforcement.
    """
    AGENT_NAME = "HRAgent"

    def __init__(self):
        self.db = db

    def get_employee_info(self, emp_id: str, principal: Optional[Principal] = None) -> Dict[str, Any]:
        """Tool: Fetches employee profile from Mock DB with authorization check."""
        if principal:
            authorize_target(emp_id, principal)
        return self.db.get_employee_info(emp_id)

    def apply_leave(
        self,
        emp_id: str,
        start_date: str,
        end_date: str,
        reason: str = "Personal",
        principal: Optional[Principal] = None
    ) -> Dict[str, Any]:
        """Tool: Mutates leave balance in Mock DB with authorization check."""
        if principal:
            authorize_target(emp_id, principal)
        actor_role = principal.role if principal else "EMPLOYEE"
        return apply_leave_with_rbac(
            emp_id=emp_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            actor_role=actor_role,
            db=self.db
        )

    def process(
        self,
        prompt: str,
        emp_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        principal: Optional[Principal] = None,
        actor_role: str = "EMPLOYEE"
    ) -> Dict[str, Any]:
        """
        Parses intent from prompt and history, executes tool(s), and formats response.
        """
        tools_used = []

        # Derive effective role and emp_id from Principal if provided
        effective_role = principal.role if principal else (actor_role or "EMPLOYEE").upper()
        effective_emp_id = principal.emp_id if principal else emp_id

        # Extract target emp_id from prompt or default to requester
        target_emp_id = None
        emp_match = re.search(r'\b(EMP\d{3})\b', prompt, re.IGNORECASE)
        if emp_match:
            target_emp_id = emp_match.group(1).upper()
        elif effective_emp_id:
            target_emp_id = effective_emp_id.strip().upper()

        prompt_lower = prompt.lower()
        is_apply_leave_intent = is_leave_application_request(prompt)

        # Enforce Account Ownership Check if targeting another employee
        if target_emp_id and effective_role != "HR":
            if effective_emp_id and target_emp_id.upper() != effective_emp_id.strip().upper():
                return {
                    "answer": "You can only apply leave for your own account.",
                    "sources": [],
                    "tools_used": [],
                    "agent_routed": self.AGENT_NAME
                }

        # Informational leave queries (e.g. "Can I take 3 days next month?", "How many leaves do I have left?")
        is_leave_information_query = bool(re.search(
            r"\b(can i take|could i take|how many|how much|remaining|balance|left)\b",
            prompt_lower
        ))

        if is_leave_information_query and not is_apply_leave_intent:
            if target_emp_id:
                tools_used.append("get_employee_info")
                info_res = self.db.get_employee_info(target_emp_id)

                if info_res["status"] == "success":
                    balance = info_res["data"]["leave_balance"]
                    name = info_res["data"]["name"]

                    if any(p in prompt_lower for p in ["can i take", "could i take"]):
                        days_match = re.search(r'(\d+)\s*days?', prompt_lower)
                        days_str = f"{days_match.group(1)} days" if days_match else "3 days"
                        answer = (
                            f"Hi {name}! You currently have {balance} day(s) of available leave. "
                            f"You can request {days_str} next month, subject to approval. "
                            f"Please provide exact dates if you want me to submit the request."
                        )
                    else:
                        answer = f"Hi {name}! You currently have {balance} day(s) of available leave."

                    return {
                        "answer": answer,
                        "sources": [],
                        "tools_used": tools_used,
                        "agent_routed": self.AGENT_NAME
                    }

        # Scenario 1: Apply Leave Operation
        if is_apply_leave_intent:
            if not target_emp_id:
                return {
                    "answer": "Could not execute leave application: Missing employee ID. Please specify your Employee ID (e.g., EMP001).",
                    "sources": [],
                    "tools_used": [],
                    "agent_routed": self.AGENT_NAME
                }

            # Parse leave dates
            try:
                start_dt, end_dt, calc_days = extract_leave_dates(prompt)
                start_date = start_dt.strftime("%Y-%m-%d")
                end_date = end_dt.strftime("%Y-%m-%d")
            except ValueError as e:
                return {
                    "answer": str(e),
                    "sources": [],
                    "tools_used": [],
                    "agent_routed": self.AGENT_NAME
                }

            # Check available balance
            info_res = self.db.get_employee_info(target_emp_id)
            if info_res["status"] == "error":
                return {
                    "answer": info_res["message"],
                    "sources": [],
                    "tools_used": [],
                    "agent_routed": self.AGENT_NAME
                }

            tools_used.append("get_employee_info")
            emp_data = info_res["data"]
            available_balance = emp_data["leave_balance"]

            if calc_days > available_balance:
                return {
                    "answer": f"Leave application rejected: Requested duration of {calc_days} day(s) exceeds your available leave balance of {available_balance} day(s).",
                    "sources": [],
                    "tools_used": tools_used,
                    "agent_routed": self.AGENT_NAME
                }

            reason = "Personal"
            reason_match = re.search(r'reason[:\s]+(["\']?)([^"\'.]+)\1', prompt, re.IGNORECASE)
            if reason_match:
                reason = reason_match.group(2).strip()

            tools_used.append("apply_leave")
            result = self.apply_leave(target_emp_id, start_date, end_date, reason, principal=principal)

            if result["status"] == "success":
                answer = f"Your leave request for {result['days_deducted']} day(s) ({start_date} to {end_date}) has been approved. Your remaining leave balance is {result['remaining_leave_balance']} day(s)."
            else:
                answer = result["message"]

            return {
                "answer": answer,
                "sources": [],
                "tools_used": tools_used,
                "agent_routed": self.AGENT_NAME
            }

        # Scenario 2: Employee Profile & Leave Balance Query
        if not target_emp_id:
            return {
                "answer": "Please provide a valid Employee ID (e.g., EMP001 for Rahul or EMP002 for Priya) to fetch HR details.",
                "sources": [],
                "tools_used": [],
                "agent_routed": self.AGENT_NAME
            }

        result = self.db.get_employee_info(target_emp_id)
        if result["status"] == "error":
            return {
                "answer": result["message"],
                "sources": [],
                "tools_used": [],
                "agent_routed": self.AGENT_NAME
            }

        tools_used.append("get_employee_info")
        if result["status"] == "success":
            data = result["data"]
            llm = get_llm()
            if llm:
                history_clean = sanitize_history(history or [])
                system_prompt = (
                    f"You are EmployeeMate, a warm, friendly, intelligent personal AI assistant.\n"
                    f"You are speaking with {data['name']}. Answer conversationally using their real-time HR data:\n"
                    f"- Name: {data['name']}\n"
                    f"- Employee ID: {data['emp_id']}\n"
                    f"- Department: {data['department']}\n"
                    f"- Role: {data['role']}\n"
                    f"- Email: {data['email']}\n"
                    f"- Available Leave Balance: {data['leave_balance']} day(s)\n"
                )
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(history_clean)
                messages.append({"role": "user", "content": prompt})

                response = invoke_llm_with_retry(llm, messages)
                answer = extract_text_from_response(response)
                if answer:
                    return {
                        "answer": answer,
                        "sources": [],
                        "tools_used": tools_used,
                        "agent_routed": self.AGENT_NAME
                    }

            prompt_lower = prompt.lower()
            if any(term in prompt_lower for term in ["how many", "balance", "leave left", "remaining", "days off"]):
                answer = f"Hi {data['name']}! You currently have {data['leave_balance']} day(s) of available leave."
            else:
                answer = (
                    f"Employee Profile for {data['name']} ({data['emp_id']}):\n"
                    f"- Department: {data['department']}\n"
                    f"- Role: {data['role']}\n"
                    f"- Email: {data['email']}\n"
                    f"- Leave Balance: {data['leave_balance']} day(s) available."
                )
        else:
            answer = result["message"]

        return {
            "answer": answer,
            "sources": [],
            "tools_used": tools_used,
            "agent_routed": self.AGENT_NAME
        }


hr_agent = HRAgent()
