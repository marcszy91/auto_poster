"""Security utilities for password hashing and credential encryption."""

import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ============================================================================
# Password Hashing (Argon2id)
# ============================================================================

# Argon2id is the recommended password hashing algorithm
# It provides resistance against GPU cracking attacks and side-channel attacks
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Management
# ============================================================================


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"sub": user_email})
        expires_delta: Token expiration time (defaults to configured value)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token (typically {"sub": user_email})
        expires_delta: Token expiration time (defaults to configured value)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Email (subject) from token if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        type_claim: str = payload.get("type")

        if email is None or type_claim != token_type:
            return None

        return email
    except JWTError:
        return None


# ============================================================================
# Email Verification Token
# ============================================================================


def generate_verification_token() -> str:
    """
    Generate a secure random verification token for email confirmation.

    Returns:
        URL-safe random token string
    """
    return secrets.token_urlsafe(32)


# ============================================================================
# Credentials Encryption (Fernet)
# ============================================================================

# For encrypting user credentials (Instagram password, API keys, etc.)
# We derive a Fernet key from the JWT secret


def _get_fernet_key() -> bytes:
    """
    Derive a Fernet encryption key from the JWT secret.

    Returns:
        Fernet-compatible 32-byte key
    """
    # Fernet requires a 32-byte base64-encoded key
    # We'll use the first 32 bytes of the JWT secret, padded/truncated as needed
    key_material = settings.jwt_secret_key.encode()

    # Ensure we have exactly 32 bytes
    if len(key_material) < 32:
        # Pad with zeros if too short
        key_material = key_material.ljust(32, b"\0")
    else:
        # Truncate if too long
        key_material = key_material[:32]

    # Base64 encode for Fernet
    return base64.urlsafe_b64encode(key_material)


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a credential using Fernet symmetric encryption.

    Args:
        plaintext: Plain text credential to encrypt

    Returns:
        Encrypted credential as string
    """
    if not plaintext:
        return ""

    fernet = Fernet(_get_fernet_key())
    encrypted_bytes = fernet.encrypt(plaintext.encode())
    return encrypted_bytes.decode()


def decrypt_credential(encrypted: str) -> str:
    """
    Decrypt a credential using Fernet symmetric encryption.

    Args:
        encrypted: Encrypted credential string

    Returns:
        Decrypted plain text credential
    """
    if not encrypted:
        return ""

    try:
        fernet = Fernet(_get_fernet_key())
        decrypted_bytes = fernet.decrypt(encrypted.encode())
        return decrypted_bytes.decode()
    except Exception:
        # If decryption fails, return empty string
        # This can happen if the encryption key changed
        return ""
