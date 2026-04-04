from __future__ import annotations


def format_amount(amount: int) -> str:
    sign = "+" if amount >= 0 else ""
    return f"{sign}{amount:,}".replace(",", " ")


def format_unsigned(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")
