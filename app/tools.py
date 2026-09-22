"""
Standalone Tool Definitions for AI Agents & RAG Pipeline
"""
from typing import Optional, List, Dict, Any
from app.rag import rag_pipeline, RAGPipeline


def search_company_documents(
    query: str,
    category: Optional[str] = None,
    top_k_initial: int = 10,
    top_n: int = 3,
    emp_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    RAG Policy Search Tool with Metadata Filtering and Two-Stage Reranking.

    Args:
        query (str): The search query or policy question.
        category (Optional[str]): Optional metadata category filter (e.g., 'wfh', 'leave', 'travel', 'it_security').
        top_k_initial (int): Initial number of vector candidates to retrieve (default: 10).
        top_n (int): Final number of reranked top chunks to return (default: 3).
        emp_id (Optional[str]): Optional Employee ID for user context.
        history (Optional[List[Dict[str, str]]]): Conversation history for context.

    Returns:
        Dict[str, Any]: Structured dictionary with answer, sources, and retrieved documents.
    """
    answer, sources = rag_pipeline.query(
        query_text=query,
        category=category,
        k_initial=top_k_initial,
        top_n=top_n,
        emp_id=emp_id,
        history=history
    )

    docs, _ = rag_pipeline.search_company_documents(
        query=query,
        category=category,
        top_k_initial=top_k_initial,
        top_n=top_n
    )

    doc_snippets = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]

    return {
        "answer": answer,
        "sources": sources,
        "documents": doc_snippets
    }


def apply_leave_with_rbac(
    emp_id: str,
    start_date: str,
    end_date: str,
    reason: str,
    actor_role: str = "EMPLOYEE",
    db = None
) -> Dict[str, Any]:
    """
    Applies leave for an employee with RBAC enforcement in Mock DB.
    """
    if db is None:
        from app.mock_db import db as mock_db
        db = mock_db

    return db.apply_leave(emp_id=emp_id, start_date=start_date, end_date=end_date, reason=reason)


def get_employee_info(employee_id: str, db=None) -> Dict[str, Any]:
    if db is None:
        from app.mock_db import db as mock_db
        db = mock_db

    return db.get_employee_info(employee_id)


def apply_leave(
    employee_id: str,
    start_date: str,
    end_date: str,
    reason: str = "Personal",
    db=None
) -> Dict[str, Any]:
    if db is None:
        from app.mock_db import db as mock_db
        db = mock_db

    return db.apply_leave(
        emp_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )


