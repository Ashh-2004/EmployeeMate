import threading
from typing import Dict, Any, Optional
from datetime import datetime


class MockDatabase:
    """
    In-memory database storing employee profiles and handling leave operations.
    Thread-safe implementation with mutation capability.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._employees: Dict[str, Dict[str, Any]] = {
            "EMP001": {
                "emp_id": "EMP001",
                "name": "Rahul",
                "department": "Engineering",
                "leave_balance": 50,
                "email": "rahul@company.com",
                "role": "Senior Software Engineer",
                "history": []
            },
            "EMP002": {
                "emp_id": "EMP002",
                "name": "Priya",
                "department": "HR",
                "leave_balance": 50,
                "email": "priya@company.com",
                "role": "HR Manager",
                "history": []
            }
        }

    def get_all_employees(self) -> Dict[str, Any]:
        """
        Fetch all employee profiles with current live state.
        """
        with self._lock:
            return {
                "status": "success",
                "data": list(self._employees.values())
            }

    def get_employee_info(self, emp_id: str) -> Dict[str, Any]:
        """
        Fetch profile details for a given employee ID.
        """
        with self._lock:
            emp_id_clean = emp_id.strip().upper()
            if emp_id_clean in self._employees:
                emp = self._employees[emp_id_clean].copy()
                return {
                    "status": "success",
                    "data": emp
                }
            return {
                "status": "error",
                "message": f"Employee ID '{emp_id}' not found in database."
            }

    def apply_leave(self, emp_id: str, start_date: str, end_date: str, reason: str = "Personal") -> Dict[str, Any]:
        """
        Mutate leave balance and log leave request for an employee.
        """
        with self._lock:
            emp_id_clean = emp_id.strip().upper() if emp_id else ""
            if not emp_id_clean or emp_id_clean not in self._employees:
                return {
                    "status": "error",
                    "message": f"Employee ID '{emp_id}' not found in database."
                }

            emp = self._employees[emp_id_clean]
            
            # Calculate duration in days
            days_requested = 1
            try:
                # Support YYYY-MM-DD format
                start_dt = datetime.strptime(start_date.strip(), "%Y-%m-%d")
                end_dt = datetime.strptime(end_date.strip(), "%Y-%m-%d")
                if end_dt < start_dt:
                    return {
                        "status": "error",
                        "message": f"End date ({end_date}) cannot be prior to start date ({start_date})."
                    }
                days_requested = (end_dt - start_dt).days + 1
            except ValueError:
                # If date format isn't YYYY-MM-DD, default to 1 day request but keep provided strings
                days_requested = 1

            current_balance = emp["leave_balance"]
            if current_balance < days_requested:
                return {
                    "status": "error",
                    "message": f"Insufficient leave balance for {emp['name']}. Requested: {days_requested} day(s), Available: {current_balance} day(s)."
                }

            # Mutate state
            emp["leave_balance"] -= days_requested
            record = {
                "start_date": start_date,
                "end_date": end_date,
                "days": days_requested,
                "reason": reason,
                "applied_at": datetime.now().isoformat()
            }
            emp["history"].append(record)

            return {
                "status": "success",
                "message": f"Successfully applied {days_requested} day(s) of leave for {emp['name']} ({emp_id_clean}) from {start_date} to {end_date}.",
                "employee_name": emp["name"],
                "emp_id": emp_id_clean,
                "days_deducted": days_requested,
                "remaining_leave_balance": emp["leave_balance"],
                "reason": reason
            }


# Singleton database instance
db = MockDatabase()
