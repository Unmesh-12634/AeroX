"""
SIH26056: Government Official Authentication & User Database Layer
Secure SQLite persistence for MoSPI, MoCA, DGCA, and DoCA Officer Credentials
"""

import os
import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from backend.config import settings

AUTH_DB_PATH = settings.DATA_DIR / "auth_users.db"

def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    # PBKDF2-HMAC-SHA256 with 100,000 iterations (OWASP standard)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

class AuthDatabase:
    def __init__(self, db_path: Path = AUTH_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_default_officers()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    designation TEXT NOT NULL,
                    ministry TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                )
            """)
            conn.commit()

    def _seed_default_officers(self):
        """Seed certified GoI demo officers across MoSPI, DGCA, MoCA, and DoCA"""
        seed_users = [
            {
                "email": "s.sharma@mospi.gov.in",
                "username": "s.sharma",
                "password": "Password@123",
                "full_name": "Dr. Sanjeev Sharma, ISS",
                "designation": "Joint Director (Price Statistics)",
                "ministry": "MoSPI"
            },
            {
                "email": "k.verma@dgca.gov.in",
                "username": "k.verma",
                "password": "Password@123",
                "full_name": "Capt. K. Verma",
                "designation": "Director General (Air Transport)",
                "ministry": "DGCA"
            },
            {
                "email": "r.iyer@moca.gov.in",
                "username": "r.iyer",
                "password": "Password@123",
                "full_name": "Rajesh Iyer, IAS",
                "designation": "Joint Secretary (Civil Aviation)",
                "ministry": "MoCA"
            },
            {
                "email": "p.mehta@doca.gov.in",
                "username": "p.mehta",
                "password": "Password@123",
                "full_name": "Pooja Mehta",
                "designation": "Deputy Commissioner (Consumer Affairs)",
                "ministry": "DoCA"
            }
        ]

        for u in seed_users:
            if not self.get_user_by_email(u["email"]):
                self.create_user(
                    email=u["email"],
                    username=u["username"],
                    password=u["password"],
                    full_name=u["full_name"],
                    designation=u["designation"],
                    ministry=u["ministry"]
                )

    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        designation: str,
        ministry: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        email_clean = email.strip().lower()
        uname = username.strip().lower() if username else email_clean.split('@')[0]
        hashed, salt = _hash_password(password)
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (
                    id, email, username, hashed_password, salt,
                    full_name, designation, ministry, created_at, last_login_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email_clean, uname, hashed, salt,
                full_name.strip(), designation.strip(), ministry.strip(), created_at, None
            ))
            conn.commit()

        return {
            "id": user_id,
            "email": email_clean,
            "username": uname,
            "full_name": full_name.strip(),
            "designation": designation.strip(),
            "ministry": ministry.strip(),
            "created_at": created_at
        }

    def authenticate(self, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        clean_id = identifier.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users WHERE email = ? OR username = ?
            """, (clean_id, clean_id))
            row = cursor.fetchone()
            if not row:
                return None

            expected_hash, _ = _hash_password(password, row["salt"])
            if secrets.compare_digest(expected_hash, row["hashed_password"]):
                # Update last login
                now_str = datetime.utcnow().isoformat()
                cursor.execute("""
                    UPDATE users SET last_login_at = ? WHERE id = ?
                """, (now_str, row["id"]))
                conn.commit()

                return {
                    "id": row["id"],
                    "email": row["email"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "designation": row["designation"],
                    "ministry": row["ministry"],
                    "created_at": row["created_at"],
                    "last_login_at": now_str
                }
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "designation": row["designation"],
                    "ministry": row["ministry"],
                    "created_at": row["created_at"],
                    "last_login_at": row["last_login_at"]
                }
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "designation": row["designation"],
                    "ministry": row["ministry"],
                    "created_at": row["created_at"],
                    "last_login_at": row["last_login_at"]
                }
        return None

auth_db = AuthDatabase()
