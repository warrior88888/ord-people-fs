from __future__ import annotations

import logging

from itsdangerous import BadSignature, TimestampSigner

logger = logging.getLogger(__name__)


class ItsDangerousSessionSigner:
    def __init__(self, secret_key: str, max_age: int) -> None:
        self._signer = TimestampSigner(secret_key, salt="session")
        self._max_age = max_age

    def sign(self, session_id: str) -> str:
        return self._signer.sign(session_id).decode()

    def unsign(self, signed: str) -> str | None:
        try:
            return self._signer.unsign(signed, max_age=self._max_age).decode()
        except BadSignature as e:
            logger.warning(
                "session_unsign_bad_signature reason=%s", e.__class__.__name__
            )
            return None
