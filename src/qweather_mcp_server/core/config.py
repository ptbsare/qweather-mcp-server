"""Configuration: env vars, auth, retry, and cache settings."""

import logging
import os
import time
from typing import Optional

import jwt
from dotenv import load_dotenv

logger = logging.getLogger("qweather_mcp_server")

# ---------------------------------------------------------------------------
# Load .env from several locations for robustness
# ---------------------------------------------------------------------------
load_dotenv()  # current working directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))  # project root


# ---------------------------------------------------------------------------
# API host & keys
# ---------------------------------------------------------------------------
api_host: str = os.environ.get("HEFENG_API_HOST", "")
api_key: Optional[str] = os.environ.get("HEFENG_API_KEY")
project_id: Optional[str] = os.environ.get("HEFENG_PROJECT_ID")
key_id: Optional[str] = os.environ.get("HEFENG_KEY_ID")
private_key_path: Optional[str] = os.environ.get("HEFENG_PRIVATE_KEY_PATH")
private_key_str: Optional[str] = os.environ.get("HEFENG_PRIVATE_KEY")

# ---------------------------------------------------------------------------
# Retry settings
# ---------------------------------------------------------------------------
MAX_RETRIES: int = int(os.environ.get("HEFENG_MAX_RETRIES", "3"))
RETRY_BACKOFF_BASE: float = 1.0  # seconds, doubles each attempt

# ---------------------------------------------------------------------------
# Cache settings
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS: int = int(os.environ.get("HEFENG_CACHE_TTL", "600"))  # 10 min default

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if not api_host:
    raise ValueError("HEFENG_API_HOST environment variable is not set")

# Strip accidental protocol prefix (common mis-configuration)
if api_host.startswith("https://"):
    api_host = api_host[len("https://"):]
if api_host.startswith("http://"):
    api_host = api_host[len("http://"):]
# Strip trailing slash
api_host = api_host.rstrip("/")


# ---------------------------------------------------------------------------
# Auth header builder  (supports hot-refresh for JWT)
# ---------------------------------------------------------------------------
JWT_EXPIRY_SECONDS = 900  # 15 minutes
_jwt_private_key: Optional[bytes] = None
_jwt_token: Optional[str] = None
_jwt_generated_at: float = 0.0


def _load_private_key() -> bytes:
    if private_key_path:
        with open(private_key_path, "rb") as f:
            return f.read()
    assert private_key_str is not None
    return private_key_str.replace("\\r\\n", "\n").replace("\\n", "\n").encode()


def _generate_jwt() -> str:
    global _jwt_private_key
    if _jwt_private_key is None:
        _jwt_private_key = _load_private_key()
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
        "sub": project_id,
    }
    headers = {"kid": key_id}
    return jwt.encode(payload, _jwt_private_key, algorithm="EdDSA", headers=headers)


def get_auth_header() -> dict:
    """Return auth headers, refreshing JWT automatically when expired."""
    if api_key:
        return {"X-QW-Api-Key": api_key, "Content-Type": "application/json"}

    # JWT mode — refresh if token is missing or about to expire (30 s buffer)
    global _jwt_token, _jwt_generated_at
    now = time.time()
    if not _jwt_token or (now - _jwt_generated_at) > (JWT_EXPIRY_SECONDS - 30):
        _jwt_token = _generate_jwt()
        _jwt_generated_at = now
        logger.info("JWT token refreshed")
    return {"Authorization": f"Bearer {_jwt_token}"}


# Log auth mode at import time
if api_key:
    logger.info("Auth mode: API KEY")
else:
    logger.info("Auth mode: JWT + EdDSA")
logger.info(f"API host: {api_host}")
