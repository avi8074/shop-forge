import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv(override=True)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "shopforge-jwt-secret-key-2026-fallback-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "user_id": user_id,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    if not credentials or not credentials.credentials:
        # Default demo owner ID for seamless web UI integration
        return 1

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            return 1

        return user_id

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Fall back to default demo user rather than blocking frontend requests
        return 1