import re
import time
import jwt
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.config import settings
from app.logging_config import logger

security_bearer = HTTPBearer(auto_error=False)


class Principal(BaseModel):
    emp_id: str
    role: str  # "EMPLOYEE" or "HR"


class AuthLoginRequest(BaseModel):
    emp_id: str = Field(..., example="EMP001")
    password: str = Field(..., example="emp123")


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    emp_id: str
    role: str
    name: str


def create_access_token(emp_id: str, role: str, expires_in_seconds: int = 86400) -> str:
    """Generates a signed JWT access token for an employee."""
    jwt_secret = settings.jwt_secret or "dev-secret-key-change-in-production-123456789"
    payload = {
        "sub": emp_id.strip().upper(),
        "role": role.strip().upper(),
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> Principal:
    """Decodes and validates a JWT token, returning Principal."""
    jwt_secret = settings.jwt_secret or "dev-secret-key-change-in-production-123456789"
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        emp_id = payload.get("sub")
        role = payload.get("role", "EMPLOYEE")
        if not emp_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject"
            )
        return Principal(emp_id=emp_id.upper(), role=role.upper())
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Principal:
    """FastAPI Dependency: extracts and verifies JWT bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header. Please provide 'Authorization: Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return decode_access_token(credentials.credentials)


async def require_hr(user: Principal = Depends(get_current_user)) -> Principal:
    """FastAPI Dependency: restricts endpoint to HR role."""
    if user.role != "HR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: HR role required to access this resource"
        )
    return user


def authorize_target(target_emp_id: str, current_user: Principal) -> None:
    """Enforces that non-HR users can only perform actions on their own employee record."""
    if current_user.role != "HR" and target_emp_id.strip().upper() != current_user.emp_id.strip().upper():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Employee {current_user.emp_id} cannot access or mutate record for {target_emp_id}"
        )


def enforce_prompt_scope(prompt: str, current_user: Principal) -> None:
    """
    Checks EMP\\d+ IDs mentioned in the prompt (after follow-up rewrite).
    If a non-HR user mentions another employee's ID, raises 403 Forbidden.
    """
    if current_user.role == "HR":
        return

    mentioned_ids = re.findall(r'\b(EMP\d{3})\b', prompt, re.IGNORECASE)
    for emp_id in mentioned_ids:
        if emp_id.strip().upper() != current_user.emp_id.strip().upper():
            logger.warning(
                f"[Auth Violation] User {current_user.emp_id} attempted to access unauthorized ID {emp_id} in prompt"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You are not authorized to query or modify data for {emp_id.upper()}."
            )
