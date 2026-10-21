from typing import Optional
from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_local_token(x_local_token: Optional[str] = Header(None)) -> str:
    """
    Validates pre-shared token from local collectors (Chrome extension, Windows watcher).
    Prevents unauthorized local processes or malicious websites from posting fake events.
    """
    if not settings.LOCAL_AUTH_TOKEN:
        return "unsecured"

    if not x_local_token or x_local_token != settings.LOCAL_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Local-Token authentication header",
        )
    return x_local_token

