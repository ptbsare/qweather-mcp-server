"""HTTP helper with retry, backoff, and auth header auto-refresh."""

import logging
import time
from typing import Any, Dict, Optional

import httpx

from qweather_mcp_server.core.config import MAX_RETRIES, RETRY_BACKOFF_BASE, get_auth_header

logger = logging.getLogger("qweather_mcp_server")

# Force HTTP/1.1 — some QWeather API endpoints return 400 on HTTP/2
_client = httpx.Client(http2=False, timeout=15)


def api_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
) -> Optional[Dict[str, Any]]:
    """
    GET *url* with query *params*, retrying up to MAX_RETRIES times.

    Returns parsed JSON dict on success, or None after all retries are exhausted.
    """
    last_err: Optional[str] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = get_auth_header()
            resp = _client.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            last_err = f"status={resp.status_code} body={resp.text[:200]}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {last_err}")
        except httpx.TimeoutException as e:
            last_err = f"timeout: {e}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} timed out: {e}")
        except httpx.RequestError as e:
            last_err = f"network error: {e}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} network error: {e}")
        except Exception as e:
            last_err = f"unexpected: {e}"
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} unexpected error: {e}")

        if attempt < MAX_RETRIES:
            sleep_s = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.info(f"Retrying in {sleep_s:.1f}s …")
            time.sleep(sleep_s)

    logger.error(f"All {MAX_RETRIES} attempts failed for {url}. Last error: {last_err}")
    return None
