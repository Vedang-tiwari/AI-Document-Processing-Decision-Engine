from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import hmac
import hashlib
import bcrypt
import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.config import settings
from backend.app.core.exceptions import UnauthorizedException, ForbiddenException

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid or expired authentication token")


def sign_webhook_payload(payload_bytes: bytes, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload verification.
    """
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


class CurrentUser:
    def __init__(self, id: str, email: str, role: str):
        self.id = id
        self.email = email
        self.role = role


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> CurrentUser:
    if not auth or not auth.credentials:
        # Development fallback / anonymous mock operator if in development without token
        if settings.APP_ENV == "development":
            return CurrentUser(
                id="00000000-0000-0000-0000-000000000001",
                email="admin@example.com",
                role="admin",
            )
        raise UnauthorizedException("Missing Authorization header")

    payload = decode_access_token(auth.credentials)
    user_id = payload.get("sub")
    email = payload.get("email", "")
    role = payload.get("role", "operator")

    if not user_id:
        raise UnauthorizedException("Token missing subject identifier")

    return CurrentUser(id=user_id, email=email, role=role)


def require_role(*required_roles: str):
    def role_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in required_roles and user.role != "admin":
            raise ForbiddenException(
                f"Role '{user.role}' is not authorized to access this resource"
            )
        return user

    return role_checker
