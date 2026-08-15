from datetime import datetime, timedelta, timezone

from app.models.auth import AuthSession
from app.services.auth import hash_password, verify_password


def test_hash_and_verify():
    stored = hash_password("secret123")
    assert stored.startswith("scrypt$")
    assert verify_password("secret123", stored)
    assert not verify_password("wrong-password", stored)
    assert not verify_password("", stored)
    assert not verify_password("secret123", "")
    assert not verify_password("secret123", "bogus$hash")
    assert not verify_password("secret123", "scrypt$zz$zz")


def test_hash_is_salted():
    assert hash_password("same-password") != hash_password("same-password")


def test_session_expiry():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expired = AuthSession(token="t1", username="u", created_at=now - timedelta(days=31))
    assert expired.is_expired()

    fresh = AuthSession(token="t2", username="u", created_at=now - timedelta(days=29))
    assert not fresh.is_expired()
