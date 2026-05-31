from __future__ import annotations


def long_str(n: int, fill: str = "x") -> str:
    return fill * n


def below_min(n: int, fill: str = "x") -> str:
    return fill * max(0, n - 1)


def above_max(n: int, fill: str = "x") -> str:
    return fill * (n + 1)


VALID_USERNAME = "alice_42"
VALID_FIRSTNAME = "Alice"
VALID_LASTNAME = "Smith"
VALID_PASSWORD = "Sup3rSecret!"
