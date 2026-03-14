import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets

from app.core.config import settings


class TokenError(ValueError):
    pass


def generate_secret_key(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def get_password_hash(password: str, salt: str | None = None) -> str:
    active_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        active_salt.encode("utf-8"),
        120000,
    )
    return f"{active_salt}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, expected_hash = hashed_password.split("$", maxsplit=1)
    except ValueError:
        return False
    calculated_hash = get_password_hash(password, salt).split("$", maxsplit=1)[1]
    return hmac.compare_digest(calculated_hash, expected_hash)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    payload_segment = _urlsafe_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(settings.secret_key.encode("utf-8"), payload_segment.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_segment}.{_urlsafe_encode(signature)}"


def decode_access_token(token: str) -> dict[str, int | str]:
    try:
        payload_segment, signature_segment = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise TokenError("Invalid or expired token") from exc

    expected_signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        payload_segment.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    actual_signature = _urlsafe_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise TokenError("Invalid or expired token")

    try:
        payload = json.loads(_urlsafe_decode(payload_segment))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TokenError("Invalid or expired token") from exc

    expires_at = payload.get("exp")
    subject = payload.get("sub")
    if not isinstance(expires_at, int) or not isinstance(subject, str):
        raise TokenError("Invalid or expired token")
    if expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("Invalid or expired token")

    return payload


def _urlsafe_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _urlsafe_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(f"{data}{padding}")
    except (ValueError, binascii.Error) as exc:
        raise TokenError("Invalid or expired token") from exc
