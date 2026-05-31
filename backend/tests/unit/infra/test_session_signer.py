from __future__ import annotations

import datetime

from freezegun import freeze_time

from ord_people.infra.auth.session_signer import ItsDangerousSessionSigner


def test_roundtrip(signer):
    sid = "abc123"
    signed = signer.sign(sid)
    assert signer.unsign(signed) == sid


def test_tampered_returns_none(signer):
    signed = signer.sign("abc")
    tampered = signed + "x"
    assert signer.unsign(tampered) is None


def test_empty_string_returns_none(signer):
    assert signer.unsign("") is None


def test_garbage_returns_none(signer):
    assert signer.unsign("not.signed.at.all") is None


def test_max_age_expiry():
    s = ItsDangerousSessionSigner(secret_key="k", max_age=1)
    with freeze_time("2026-01-01 00:00:00") as frozen:
        signed = s.sign("abc")
        frozen.tick(delta=datetime.timedelta(seconds=5))
        assert s.unsign(signed) is None
