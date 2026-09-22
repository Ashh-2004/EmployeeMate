import unittest
from unittest.mock import patch, MagicMock
from app.agents.orchestrator import orchestrator
from app.auth import Principal
from app.mock_db import MockDatabase


class TestAssessmentScenarios(unittest.TestCase):

    def setUp(self):
        orchestrator.hr_agent.db = MockDatabase()

    def test_wfh_policy_returns_source(self):
        result = orchestrator.route_and_execute("What is the WFH policy?")
        self.assertIn("answer", result)
        self.assertIn("sources", result)
        self.assertTrue(len(result["sources"]) > 0 or "wfh" in result["answer"].lower())

    def test_pet_insurance_returns_not_found(self):
        result = orchestrator.route_and_execute("Does the company provide pet insurance?")
        self.assertIn("couldn't find information", result["answer"].lower())

    def test_employee_balance_uses_tool(self):
        result = orchestrator.route_and_execute(
            "How many leaves do I have?",
            emp_id="EMP001",
            principal=Principal(emp_id="EMP001", role="EMPLOYEE")
        )
        self.assertIn("50", result["answer"])
        self.assertIn("get_employee_info", result["tools_used"])

    def test_multi_tool_query(self):
        result = orchestrator.route_and_execute(
            "What is the leave policy and how many leaves does EMP001 have?",
            emp_id="EMP001",
            principal=Principal(emp_id="EMP001", role="EMPLOYEE")
        )
        self.assertIn("answer", result)
        self.assertIn("get_employee_info", result["tools_used"])

    def test_apply_leave_updates_balance(self):
        result = orchestrator.route_and_execute(
            "Apply leave for EMP001 from 20 Sept to 22 Sept",
            emp_id="EMP001",
            principal=Principal(emp_id="EMP001", role="EMPLOYEE")
        )
        self.assertIn("approved", result["answer"].lower())
        self.assertIn("47", result["answer"])
        self.assertIn("get_employee_info", result["tools_used"])
        self.assertIn("apply_leave", result["tools_used"])

    def test_followup_understands_leave_context(self):
        history = [
            {"role": "user", "content": "How many leaves do I have?"},
            {"role": "assistant", "content": "You have 50 days remaining."},
        ]

        result = orchestrator.route_and_execute(
            "Can I take 3 days next month?",
            emp_id="EMP001",
            principal=Principal(emp_id="EMP001", role="EMPLOYEE"),
            history=history,
        )

        self.assertIn("leave", result["answer"].lower())
        self.assertTrue("date" in result["answer"].lower() or "50" in result["answer"])
        self.assertIn("get_employee_info", result["tools_used"])


if __name__ == "__main__":
    unittest.main()
