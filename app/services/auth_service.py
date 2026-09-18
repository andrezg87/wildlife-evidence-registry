from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.repositories import user_repository

JWT_ALGORITHM = "HS256"


def _verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def _create_access_token(user_id: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": user_id, "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


async def authenticate(username: str, password: str) -> str | None:
    user = await user_repository.get_by_username(username)
    if user is None:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return _create_access_token(str(user["id"]), user["role"])
