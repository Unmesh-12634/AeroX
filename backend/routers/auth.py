"""
SIH26056: Government Official Authentication Router
Endpoints for Officer Login, Sign Up, Profile, and Demo Role Credentials
"""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header, Response, Cookie
from backend.db.auth_db import auth_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory session token store: token -> user_dict
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

class LoginRequest(BaseModel):
    identifier: Optional[str] = Field(None, description="Official .gov.in email or username")
    email: Optional[str] = Field(None, description="Official .gov.in email")
    username: Optional[str] = Field(None, description="Official username")
    password: str = Field(..., description="Officer secure password")

class SignUpRequest(BaseModel):
    email: str = Field(..., description="Official .gov.in email address")
    password: str = Field(..., description="Password (minimum 6 chars)")
    full_name: str = Field(..., description="Official title and name, e.g., 'Dr. Sanjeev Sharma, ISS'")
    designation: str = Field(..., description="Official designation, e.g., 'Joint Director (Price Statistics)'")
    ministry: str = Field(..., description="MoSPI | MoCA | DGCA | DoCA")
    username: Optional[str] = None

@router.post("/login")
def login_officer(req: LoginRequest, response: Response) -> Dict[str, Any]:
    ident = req.identifier or req.email or req.username
    if not ident:
        raise HTTPException(status_code=422, detail="Official email or username is required.")
    user = auth_db.authenticate(ident, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid official credentials. Ensure your .gov.in email and password are correct.")

    session_token = str(uuid.uuid4())
    ACTIVE_SESSIONS[session_token] = user

    response.set_cookie(
        key="officer_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )

    return {
        "status": "authenticated",
        "session_token": session_token,
        "token": session_token,
        "officer": user,
        "message": f"Welcome, {user['full_name']} ({user['ministry']})"
    }

@router.post("/signup")
def signup_officer(req: SignUpRequest, response: Response) -> Dict[str, Any]:
    # Check if user already exists
    existing = auth_db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="An official account with this .gov.in email address is already registered.")

    if len(req.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    valid_ministries = ["MoSPI", "MoCA", "DGCA", "DoCA"]
    ministry_clean = req.ministry.strip()
    if ministry_clean not in valid_ministries:
        ministry_clean = "MoSPI"

    user = auth_db.create_user(
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        designation=req.designation,
        ministry=ministry_clean,
        username=req.username
    )

    session_token = str(uuid.uuid4())
    ACTIVE_SESSIONS[session_token] = user

    response.set_cookie(
        key="officer_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )

    return {
        "status": "registered",
        "session_token": session_token,
        "token": session_token,
        "officer": user,
        "message": f"Official credentials issued for {user['full_name']} ({user['ministry']})"
    }

@router.post("/logout")
def logout_officer(response: Response, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        ACTIVE_SESSIONS.pop(token, None)

    response.delete_cookie(key="officer_session")
    return {
        "status": "unauthenticated",
        "message": "Officer session securely cleared and terminated."
    }

@router.get("/me")
def get_current_officer(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        user = ACTIVE_SESSIONS.get(token)
        if user:
            return {"authenticated": True, "officer": user}

    return {"authenticated": False, "officer": None}

@router.get("/demo-officers")
def get_demo_officers() -> Dict[str, Any]:
    """Returns pre-certified official demo credentials for instant hackathon evaluation"""
    return {
        "accounts": [
            {
                "email": "s.sharma@mospi.gov.in",
                "password": "Password@123",
                "full_name": "Dr. Sanjeev Sharma, ISS",
                "designation": "Joint Director (Price Statistics)",
                "ministry": "MoSPI",
                "clearance": "National CPI & APIx Lead"
            },
            {
                "email": "k.verma@dgca.gov.in",
                "password": "Password@123",
                "full_name": "Capt. K. Verma",
                "designation": "Director General (Air Transport)",
                "ministry": "DGCA",
                "clearance": "Tariff Regulatory Oversight"
            },
            {
                "email": "r.iyer@moca.gov.in",
                "password": "Password@123",
                "full_name": "Rajesh Iyer, IAS",
                "designation": "Joint Secretary (Civil Aviation)",
                "ministry": "MoCA",
                "clearance": "Executive Command Access"
            },
            {
                "email": "p.mehta@doca.gov.in",
                "password": "Password@123",
                "full_name": "Pooja Mehta",
                "designation": "Deputy Commissioner (Consumer Affairs)",
                "ministry": "DoCA",
                "clearance": "Consumer Fare Protection"
            }
        ]
    }
