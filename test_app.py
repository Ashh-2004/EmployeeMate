"""
Integration and End-to-End Test Suite for Agentic Employee AI Assistant
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.mock_db import MockDatabase
from app.rag import rag_pipeline, RAGPipeline
from app.agents.knowledge_agent import knowledge_agent
from app.agents.hr_agent import hr_agent
from app.agents.orchestrator import orchestrator
from app.main import app
from fastapi.testclient import TestClient


class TestEmployeeAIAssistant(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.mock_db = MockDatabase()

    def test_01_mock_db_operations(self):
        """Test Mock Database get_employee_info and apply_leave mutation"""
        info_rahul = self.mock_db.get_employee_info("EMP001")
        self.assertEqual(info_rahul["status"], "success")
        self.assertEqual(info_rahul["data"]["name"], "Rahul")
        self.assertEqual(info_rahul["data"]["leave_balance"], 50)

        info_priya = self.mock_db.get_employee_info("EMP002")
        self.assertEqual(info_priya["status"], "success")
        self.assertEqual(info_priya["data"]["name"], "Priya")
        self.assertEqual(info_priya["data"]["leave_balance"], 50)

        # Apply 2 days leave for EMP001
        res = self.mock_db.apply_leave("EMP001", "2026-10-01", "2026-10-02", "Vacation")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["remaining_leave_balance"], 48)

        # Verify balance updated in DB
        updated_info = self.mock_db.get_employee_info("EMP001")
        self.assertEqual(updated_info["data"]["leave_balance"], 48)

    def test_02_rag_pipeline_retrieval(self):
        """Test RAG pipeline indexing and strict default response for missing info"""
        answer, sources = rag_pipeline.query("What is the WFH policy?")
        self.assertIn("wfh_policy.txt", sources)
        self.assertNotEqual(answer, "")

        # Missing context test (Guideline 2)
        missing_answer, missing_sources = rag_pipeline.query("What is the company stock option vesting period?")
        self.assertIn("I couldn't find information about", missing_answer)
        self.assertEqual(missing_sources, [])

    def test_03_knowledge_agent(self):
        """Test KnowledgeAgent processing and tool reporting"""
        res = knowledge_agent.process("What is the daily per diem allowance for domestic travel?")
        self.assertEqual(res["agent_routed"], "KnowledgeAgent")
        self.assertIn("RAG_Policy_Search", res["tools_used"])
        self.assertIn("travel_policy.txt", res["sources"])

    def test_04_hr_agent(self):
        """Test HRAgent queries and mutations"""
        res_info = hr_agent.process("Fetch profile for EMP002")
        self.assertEqual(res_info["agent_routed"], "HRAgent")
        self.assertIn("get_employee_info", res_info["tools_used"])
        self.assertIn("Priya", res_info["answer"])

        res_leave = hr_agent.process("Apply leave for EMP002 from 2026-11-10 to 2026-11-11 reason: Personal", emp_id="EMP002")
        self.assertEqual(res_leave["agent_routed"], "HRAgent")
        self.assertIn("apply_leave", res_leave["tools_used"])

    def test_05_orchestrator_multi_agent(self):
        """Test Orchestrator router routing to BOTH agents for hybrid queries"""
        res = orchestrator.route_and_execute(
            "What is the IT security policy and check leave balance for EMP001?"
        )
        self.assertEqual(res["agent_routed"], "Orchestrator_MultiAgent")
        self.assertIn("it_security_policy.txt", res["sources"])
        self.assertIn("RAG_Policy_Search", res["tools_used"])
        self.assertIn("get_employee_info", res["tools_used"])

    def test_06_fastapi_endpoints(self):
        """Test FastAPI GET /health and POST /chat endpoints"""
        health_resp = self.client.get("/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json()["status"], "healthy")

        from app.auth import create_access_token
        emp_token = create_access_token("EMP001", "EMPLOYEE")
        headers = {"Authorization": f"Bearer {emp_token}"}

        chat_payload = {
            "prompt": "What is the annual leave policy?",
            "emp_id": "EMP001"
        }
        chat_resp = self.client.post("/chat", headers=headers, json=chat_payload)
        self.assertEqual(chat_resp.status_code, 200)

        data = chat_resp.json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertIn("tools_used", data)
        self.assertIn("agent_routed", data)
        self.assertIsInstance(data["sources"], list)
        self.assertIsInstance(data["tools_used"], list)

    def test_07_apply_multi_day_leave(self):
        """Test applying multi-day leave (e.g. 10 days) deducts exact requested days"""
        res = hr_agent.process("Apply leave for EMP001 from 2026-10-01 to 2026-10-10 reason: Vacation", emp_id="EMP001")
        self.assertEqual(res["agent_routed"], "HRAgent")
        self.assertIn("apply_leave", res["tools_used"])
        self.assertIn("10 day(s)", res["answer"])

    def test_08_leave_exceeds_balance_rejection(self):
        """Test pre-check rejection when requested days exceed available balance (Guideline 3)"""
        res = hr_agent.process("Apply leave for EMP002 from 2026-10-01 to 2026-11-29 reason: Sabbatical", emp_id="EMP002")
        self.assertEqual(res["agent_routed"], "HRAgent")
        self.assertIn("rejected", res["answer"].lower())
        self.assertIn("exceeds your available leave balance", res["answer"])

    def test_09_pure_policy_query_does_not_trigger_hr_agent(self):
        """Test pure policy query routes strictly to KnowledgeAgent without appending HR profile data"""
        res = orchestrator.route_and_execute(
            prompt="What is the policy for bringing pets to the office?",
            emp_id="EMP002"
        )
        self.assertEqual(res["agent_routed"], "KnowledgeAgent")
        self.assertNotIn("Employee Profile for Priya", res["answer"])
        self.assertIn("I couldn't find information about", res["answer"])

    def test_10_metadata_filtering_and_reranking(self):
        """Test metadata filtering and two-stage reranking tool search_company_documents"""
        from app.tools import search_company_documents

        # Test Metadata Filtering (filtering strictly by 'wfh' category)
        res_wfh = search_company_documents(query="What are core hours?", category="wfh")
        self.assertEqual(res_wfh["sources"], ["wfh_policy.txt"])
        self.assertTrue(len(res_wfh["documents"]) <= 3)

        # Test Metadata Filtering for 'travel' category
        res_travel = search_company_documents(query="What is the per diem?", category="travel")
        self.assertEqual(res_travel["sources"], ["travel_policy.txt"])

        # Test Reranker candidate scoring without category filter (fetches 10, reranks to top 3)
        res_unfiltered = search_company_documents(query="VPN encryption requirement", category=None, top_k_initial=10, top_n=3)
        self.assertIn("it_security_policy.txt", res_unfiltered["sources"] + [doc["metadata"].get("file_name") for doc in res_unfiltered["documents"]])
        self.assertTrue(len(res_unfiltered["documents"]) <= 3)

    def test_11_rbac_account_ownership_check(self):
        """Test non-HR/ADMIN users are blocked from applying leave for other accounts"""
        # Refusal when EMPLOYEE role tries to act on another emp_id
        res_refused = orchestrator.route_and_execute(
            prompt="Apply leave for EMP002 from 2026-10-01 to 2026-10-02",
            emp_id="EMP001",
            actor_role="EMPLOYEE"
        )
        self.assertEqual(res_refused["answer"], "You can only apply leave for your own account.")
        self.assertEqual(res_refused["tools_used"], [])

        # Allowed when actor_role is HR
        res_hr = orchestrator.route_and_execute(
            prompt="Apply leave for EMP002 from 2026-10-01 to 2026-10-02",
            emp_id="EMP001",
            actor_role="HR"
        )
        self.assertIn("apply_leave", res_hr["tools_used"])

    def test_12_unknown_employee_id_handling(self):
        """Test apply_leave returns error for unknown employee ID"""
        db_res = self.mock_db.apply_leave("EMP999", "2026-10-01", "2026-10-02", "Vacation")
        self.assertEqual(db_res["status"], "error")
        self.assertIn("not found in database", db_res["message"])

        res_unknown = orchestrator.route_and_execute(
            prompt="Apply leave for EMP999 from 2026-10-01 to 2026-10-02",
            emp_id="EMP999",
            actor_role="EMPLOYEE"
        )
        self.assertIn("not found in database", res_unknown["answer"])
        self.assertEqual(res_unknown["tools_used"], [])


if __name__ == "__main__":
    unittest.main()


