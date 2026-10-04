import secrets
from collections.abc import Callable
from typing import Annotated

from fastapi import Header, HTTPException


def admin_key_dependency(expected: str | None) -> Callable[..., None]:
    """Require an X-Admin-Key header matching `expected`; allow everything when no key is set."""

    def check(x_admin_key: Annotated[str | None, Header()] = None) -> None:
        if expected is None:
            return
        if x_admin_key is None:
            raise HTTPException(status_code=401, detail="Admin key required")
        if not secrets.compare_digest(x_admin_key.encode(), expected.encode()):
            raise HTTPException(status_code=403, detail="Invalid admin key")

    return check
