from __future__ import annotations

from unittest.mock import MagicMock

from ord_people.db.session import make_engine, make_session_factory


def test_make_engine_uses_settings():
    settings = MagicMock()
    settings.postgres.url = "postgresql+asyncpg://u:p@localhost/db"
    settings.postgres.pool_size = 5
    settings.postgres.max_overflow = 10
    settings.app.debug = False
    engine = make_engine(settings)
    assert engine is not None
    factory = make_session_factory(engine)
    assert factory is not None
