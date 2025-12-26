import re

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALLOWED_SPECIALS = "!@#$%^&*"
SPECIAL_PATTERN = f"[{re.escape(ALLOWED_SPECIALS)}]"


def validate_password(password: str):
    if not (8 <= len(password) <= 16):
        raise ValueError("Password must be 8-16 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(SPECIAL_PATTERN, password):
        raise ValueError(
            f"Password must contain at least one special character from: {ALLOWED_SPECIALS}"  # noqa: E501
        )

    if re.search(r"[^A-Za-z0-9" + re.escape(ALLOWED_SPECIALS) + r"]", password):  # noqa: E501
        raise ValueError("Password contains invalid characters")

    return True


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
